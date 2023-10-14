from django.core.paginator import Paginator
from django.db.models import F, Case, When

from jobs.models import Item, ExperienceLevel, Job


def get_job_postings(job_postings, user_id, list_parameter=None):
    if list_parameter is None or list_parameter == "all":
        pass
    elif list_parameter == "inbox":
        job_postings = job_postings.exclude(item__list__name='Archived')
    elif list_parameter == 'archived':
        job_postings = job_postings.filter(item__list__name='Archived')

        # necessary to remove any jobs that have entries in any other non-Archived lists
        job_postings = job_postings.exclude(item__in=Item.objects.all().exclude(list__name="Archived"))
    elif f"{list_parameter}".isdigit():
        job_postings = job_postings.filter(item__list_id=int(list_parameter), item__list__user_id=user_id)


    below_mid_senior_level_jobs = job_postings.exclude(joblocation__experience_level__gt=ExperienceLevel.Associate.value)
    ordered_below_mid_senior_level_job_postings = below_mid_senior_level_jobs.order_by(
        F('joblocation__easy_apply').desc(nulls_last=True), F('joblocation__date_posted').desc(nulls_last=True),
        F('joblocation__experience_level').desc(nulls_last=True),
        'company_name', 'job_title', 'id'
    )

    pk_list = []
    easy_apply_ordered_below_mid_senior_level_job_posting_pk_list = []
    non_easy_apply_ordered_below_mid_senior_level_job_posting_pk_list = []
    for ordered_below_mid_senior_level_job_posting in ordered_below_mid_senior_level_job_postings:
        if ordered_below_mid_senior_level_job_posting.id not in pk_list:
            if ordered_below_mid_senior_level_job_posting.has_easy_apply:
                easy_apply_ordered_below_mid_senior_level_job_posting_pk_list.append(
                    ordered_below_mid_senior_level_job_posting.id
                )
            else:
                non_easy_apply_ordered_below_mid_senior_level_job_posting_pk_list.append(
                    ordered_below_mid_senior_level_job_posting.id
                )
            pk_list.append(ordered_below_mid_senior_level_job_posting.id)

    above_associate_level_jobs = job_postings.filter(joblocation__experience_level__gt=ExperienceLevel.Associate.value)
    ordered_above_associate_level_jobs_postings = above_associate_level_jobs.order_by(
        F('joblocation__easy_apply').desc(nulls_last=True), F('joblocation__date_posted').desc(nulls_last=True),
        F('joblocation__experience_level').desc(nulls_last=True),
        'company_name', 'job_title', 'id'
    )

    easy_apply_ordered_above_associate_level_jobs_posting_pk_list = []
    non_easy_apply_ordered_above_associate_level_jobs_posting_pk_list = []
    for ordered_above_associate_level_jobs_posting in ordered_above_associate_level_jobs_postings:
        if ordered_above_associate_level_jobs_posting.id not in pk_list:
            if ordered_above_associate_level_jobs_posting.has_easy_apply:
                easy_apply_ordered_above_associate_level_jobs_posting_pk_list.append(
                    ordered_above_associate_level_jobs_posting.id
                )
            else:
                non_easy_apply_ordered_above_associate_level_jobs_posting_pk_list.append(
                    ordered_above_associate_level_jobs_posting.id
                )
            pk_list.append(ordered_above_associate_level_jobs_posting.id)

    preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(pk_list)])
    job_postings = Job.objects.all().filter(pk__in=pk_list).order_by(preserved)

    number_of_easy_apply_below_mid_senior_job_postings = len(easy_apply_ordered_below_mid_senior_level_job_posting_pk_list)
    number_of_non_easy_apply_below_mid_senior_job_postings = len(non_easy_apply_ordered_below_mid_senior_level_job_posting_pk_list)

    number_of_easy_apply_above_associate_job_postings = len(easy_apply_ordered_above_associate_level_jobs_posting_pk_list)
    number_of_non_easy_apply_above_associate_job_postings = len(non_easy_apply_ordered_above_associate_level_jobs_posting_pk_list)

    return (
        Paginator(job_postings, 25), number_of_easy_apply_below_mid_senior_job_postings,
        number_of_non_easy_apply_below_mid_senior_job_postings, number_of_easy_apply_above_associate_job_postings,
        number_of_non_easy_apply_above_associate_job_postings
    )

