from project.models import PublishedProject, PublishedAuthor, PublishedPublication

import csv

def search_project_text_for_str(project, search_text):
    """
    search for a string in the text from a PhysioNet project
    """
    if project.resource_type_id == 0:
        sections = ['title', 'abstract', 'background', 'methods', 'content_description', 'usage_notes', 'conflicts_of_interest', 'version', 'short_description']
    elif project.resource_type_id == 1:
        sections = ['title', 'abstract', 'background', 'content_description', 'usage_notes', 'installation', 'conflicts_of_interest', 'version', 'short_description']
    elif project.resource_type_id == 2:
        sections = ['title', 'abstract', 'background', 'methods', 'content_description', 'usage_notes', 'conflicts_of_interest', 'version', 'short_description']
    elif project.resource_type_id == 3:
        sections = ['title', 'abstract', 'background', 'methods', 'content_description', 'usage_notes', 'installation', 'conflicts_of_interest', 'version', 'short_description']
    else:
        sections = None
    text = ''
    if project.is_legacy:
        text = project.full_description
    else:
        for section in sections:
            text = text + ' ' + getattr(project, section, None)
    found_text = None
    if search_text in text:
        start_idx = text.find(search_text)
        # Extract a passage of 100 characters around the search_text
        start_passage = max(0, start_idx - 50)
        end_passage = min(len(text), start_idx + 50)
        found_text = text[start_passage:end_passage]
    return found_text


# Get all of the projects on PhysioNet
all_projs = PublishedProject.objects.all()
rows = []
for project in all_projs:
    author_list = project.author_list()
    # Get the citation for a paper published by the authors
    citation = PublishedPublication.objects.filter(project=project)
    authors = []
    # Note - some projects don't have authors listed so these projects are getting skipped
    for author in author_list:
        # Get all of the fields of interest from the project
        if citation:
            citation1 = citation[0]
            rows.append([project.id, project.version, project.title, project.creation_datetime, project.publish_datetime, project.doi, search_project_text_for_str(project, "NIH"), search_project_text_for_str(project, "NIBIB"), search_project_text_for_str(project, "NHLBI"), author.id, author.get_full_name(), author.user.join_date, citation1.citation, citation1.url])
        else:
            rows.append([project.id, project.version, project.title, project.creation_datetime, project.publish_datetime, project.doi, search_project_text_for_str(project, "NIH"), search_project_text_for_str(project, "NIBIB"), search_project_text_for_str(project, "NHLBI"), author.id, author.get_full_name(), author.user.join_date])

# Save to a CSV table
with open('projects_table.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['project_id', 'project_version', 'project_title', 'project_creation_datetime', 'project_publish_datetime', 'project_doi', 'nih_text', 'nibib_text', 'nhlbi_text', 'author_id', 'author_name', 'author_join_date', 'project_citation', 'project_citation_url'])
    for row in rows:
        writer.writerow(row)
