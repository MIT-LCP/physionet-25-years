from project.models import PublishedProject, PublishedAuthor, PublishedPublication

import csv

def search_project_text_for_str(obj, search_text):
    if obj.resource_type_id == 0:
        sections = ['title', 'abstract', 'background', 'methods', 'content_description', 'usage_notes', 'conflicts_of_interest', 'version', 'short_description']
    elif obj.resource_type_id == 1:
        sections = ['title', 'abstract', 'background', 'content_description', 'usage_notes', 'installation', 'conflicts_of_interest', 'version', 'short_description']
    elif obj.resource_type_id == 2:
        sections = ['title', 'abstract', 'background', 'methods', 'content_description', 'usage_notes', 'conflicts_of_interest', 'version', 'short_description']
    elif obj.resource_type_id == 3:
        sections = ['title', 'abstract', 'background', 'methods', 'content_description', 'usage_notes', 'installation', 'conflicts_of_interest', 'version', 'short_description']
    else:
        sections = None
    text = ''
    if obj.is_legacy:
        text = obj.full_description
    else:
        for section in sections:
            text = text + ' ' + getattr(obj, section, None)
    found_text = None
    if search_text in text:
        start_idx = text.find(search_text)
        # Extract a passage of 100 characters around the search_text
        start_passage = max(0, start_idx - 50)
        end_passage = min(len(text), start_idx + 50)
        found_text = text[start_passage:end_passage]
    return found_text


all_projs = PublishedProject.objects.all()
rows = []
for obj in all_projs:
    author_list = obj.author_list()
    citation = PublishedPublication.objects.filter(project=obj)
    authors = []
    # Note - some projects don't have authors listed so these projects are getting skipped
    for author in author_list:
        if citation:
            citation1 = citation[0]
            rows.append([obj.id, obj.version, obj.title, obj.creation_datetime, obj.publish_datetime, obj.doi, search_project_text_for_str(obj, "NIH"), search_project_text_for_str(obj, "NIBIB"), search_project_text_for_str(obj, "NHLBI"), author.id, author.get_full_name(), author.user.join_date, citation1.citation, citation1.url])
        else:
            rows.append([obj.id, obj.version, obj.title, obj.creation_datetime, obj.publish_datetime, obj.doi, search_project_text_for_str(obj, "NIH"), search_project_text_for_str(obj, "NIBIB"), search_project_text_for_str(obj, "NHLBI"), author.id, author.get_full_name(), author.user.join_date])

with open('projects_table.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['project_id', 'project_version', 'project_title', 'project_creation_datetime', 'project_publish_datetime', 'project_doi', 'nih_text', 'nibib_text', 'nhlbi_text', 'author_id', 'author_name', 'author_join_date', 'project_citation', 'project_citation_url'])
    for row in rows:
        writer.writerow(row)
