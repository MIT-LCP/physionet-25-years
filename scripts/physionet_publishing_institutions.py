from project.models import PublishedProject, PublishedPublication, PublishedAuthor, PublishedAffiliation

import csv
from django.utils import timezone


date_from = timezone.datetime(2023, 8, 15, 12, 0, 0, tzinfo=timezone.get_current_timezone())
pub1yr = PublishedProject.objects.filter(publish_datetime__gte=date_from)
rows=[]
for proj in pub1yr:
    author = PublishedAuthor.objects.get(project=proj, user=proj.submitting_user())
    all_emails = author.user.get_emails()
    affiliation = PublishedAffiliation.objects.filter(author=author)
    afilliation_values = [entry for entry in affiliation.values('name')] 
    rows.append([proj.title, proj.publish_datetime, author.user.email, afilliation_values, all_emails])

with open('publishing_email_last_year.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['project', 'published_datetime', 'primary_author_email', 'affiliations', 'all_emails'])
    for row in rows:
        writer.writerow(row)
