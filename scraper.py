import os
import re
import shutil

import es

from git.repo.base import Repo

import markdown_inserter

WIKI_URL = "https://github.com/{}/{}/{}/{}"
GIT_WIKI_URL = "git@github.com:{}/{}.wiki.git"

URL = "https://github.com/{}/{}/{}/{}"
GIT_URL = "git@github.com:{}/{}.git"

# Facet groups
FACET_GROUP_LOGS = "logs"
FACET_GROUP_DEVOPS = "devops"
FACET_GROUP_INFRA = "infra"
FACET_GROUP_SE = "solution engineers"

# Facets
FACET_DEVOPS_WIKI = "devops wiki"
FACET_DEVOPS_REPO = "devops repo"
FACET_LOGS_OPS_REPO = "logs ops repo"
FACET_LOGS_BACKEND_REPO = "logs backend repo"
FACET_LOGS_BACKEND_WIKI = "logs backend wiki"
FACET_LOGS_ES_TOOLBOX_REPO = "es toolbox repo"
FACET_INFRA_DOC = "infra doc"
FACET_SE_WIKI = "solution engineers wiki"


FACET_GROUPS = {
    FACET_GROUP_LOGS: [
        FACET_LOGS_OPS_REPO,
        FACET_LOGS_BACKEND_REPO,
        FACET_LOGS_BACKEND_WIKI
    ],
    FACET_GROUP_DEVOPS: [
        FACET_DEVOPS_WIKI,
        FACET_DEVOPS_REPO
    ],
    FACET_GROUP_INFRA: [
        FACET_INFRA_DOC
    ],
    FACET_GROUP_SE: [
        FACET_SE_WIKI
    ]
}

CONTENT_TO_INDEX = {
    # type, org/user, repo, url_prefix, facet name, facet group

    ('wiki', 'Datadog', 'devops', 'wiki', FACET_DEVOPS_WIKI, FACET_GROUP_DEVOPS),
    ('repo', 'Datadog', 'devops', 'tree/prod', FACET_DEVOPS_REPO, FACET_GROUP_DEVOPS),
    ('repo', 'Datadog', 'logs-ops', 'tree/master', FACET_LOGS_OPS_REPO, FACET_GROUP_LOGS),
    ('repo', 'Datadog', 'logs-backend', 'tree/prod', FACET_LOGS_BACKEND_REPO, FACET_GROUP_LOGS),
    ('wiki', 'Datadog', 'logs-backend', 'wiki', FACET_LOGS_BACKEND_WIKI, FACET_GROUP_LOGS),
    ('hugo', 'Datadog', 'infra-docs', 'tree/master', FACET_INFRA_DOC, FACET_GROUP_INFRA),
    ('wiki', 'Datadog', 'se-docs', 'wiki', FACET_SE_WIKI, FACET_GROUP_SE),
    ('repo', 'Datadog', 'elasticsearch-toolbox', 'tree/master', FACET_LOGS_ES_TOOLBOX_REPO, FACET_GROUP_LOGS),
}

HUGO_URLS = {
    'infra-docs': 'https://infra-docs.us1.prod.dog/'
}


def clone_all_resources(all_content):
    [clone_resource(c) for c in all_content]


def clone_resource(content_to_index):
    content_type, user, repo, _, _, _ = content_to_index

    dest_folder = "./{}_{}_{}".format(user, repo, content_type)
    url = ""

    if content_type == 'wiki':
        url = GIT_WIKI_URL.format(user, repo)

    elif content_type == 'repo' or content_type == 'hugo':
        url = GIT_URL.format(user, repo)

    # clear the dest directory if it exists
    shutil.rmtree(dest_folder, ignore_errors=True)

    print('Cloning {} into folder {} ...'.format(url, dest_folder))
    Repo.clone_from(url, dest_folder)
    print('Cloning successful!')


# For crawling wiki in repos
def get_all_wiki_page_content(user, repo, url_prefix):
    dest_folder = "./{}_{}_wiki".format(user, repo)

    for path in _get_all_files_path(dest_folder):
        file = open(path, "r")
        link_path = path\
            .replace(dest_folder + '/', '')\
            .replace('.md', '')\
            .rsplit('/', 1)[-1]  # Get last part of the url after last /

        yield {
            'title': link_path.replace('-', ' '),
            'url': WIKI_URL.format(user, repo, url_prefix, link_path),
            'content': file.read()
        }


# For crawling repos
def get_all_repo_page_content(user, repo, url_prefix):
    dest_folder = "./{}_{}_repo".format(user, repo)

    for path in _get_all_files_path(dest_folder):
        file = open(path, "r")
        link_path = path.replace(dest_folder + '/', '')

        yield {
            'title': link_path.replace('.md', ''),
            'url': URL.format(user, repo, url_prefix, link_path),
            'content': file.read()
        }


def _get_all_files_path(path):
    files = []

    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            if not file.startswith('_') and file.endswith('.md'):
                files.append(os.path.join(r, file))

    return files


# For hugo repos (generated doc using hugo)
def get_all_hugo_repo_page_content(user, repo, url_prefix):
    dest_folder = "./{}_{}_hugo/content".format(user, repo)  # we go in the content folder
    url = HUGO_URLS.get(repo)

    if url is None:
        raise Exception("You must specify the url poiting to the hosted hugo doc")

    for path in _get_all_files_path_hugo(dest_folder):
        file = open(path, "r")
        link_path = path.replace(dest_folder + '/', '')
        title = link_path\
            .replace('.md', '')\
            .replace('/_index', '')\
            .replace('_index', '')
        full_url = url + title.lower()

        if title == '':
            title = repo
            full_url = url

        # we remove the hugo template descriptive part (title name, description)
        content = file.read()
        content = re.sub(r'---[\s\S]*?title:[\s\S]*?---', '', content)

        yield {
            'title': title,
            'url': full_url,
            'content': content
        }


def _get_all_files_path_hugo(path):
    files = []

    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            if file.endswith('.md'):
                files.append(os.path.join(r, file))

    return files


GET_PAGE_CONTENT = {
    'wiki': get_all_wiki_page_content,
    'repo': get_all_repo_page_content,
    'hugo': get_all_hugo_repo_page_content
}


if __name__ == '__main__':
    # Clone all the repos
    clone_all_resources(CONTENT_TO_INDEX)

    # Recreate all the ES indexes
    es.delete()
    es.create()

    #  Insert  all the resources
    for content in CONTENT_TO_INDEX:
        content_type, user, repo, url_prefix, facet_name, facet_group = content

        content_getter_f = GET_PAGE_CONTENT[content_type]

        for content in content_getter_f(user, repo, url_prefix):
            markdown_inserter.insert_markdown_doc(facet_name, facet_group, content['content'], content['title'], content['url'])
            print('Inserted {} file {} | url: {}'.format(content_type, content['title'], content['url']))
