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


CONTENT_TO_INDEX = {
    ('wiki', 'Datadog', 'devops', 'wiki'),
    ('repo', 'Datadog', 'devops', 'tree/prod'),
    ('repo', 'Datadog', 'logs-ops', 'tree/master'),
    ('repo', 'Datadog', 'logs-backend', 'tree/prod'),
    ('wiki', 'Datadog', 'logs-backend', 'wiki'),
    ('hugo', 'Datadog', 'infra-docs', 'tree/master')
}

HUGO_URLS = {
    'infra-docs': 'https://infra-docs.us1.prod.dog/'
}


def clone_all_resources(all_content):
    [clone_resource(c) for c in all_content]


def clone_resource(content_to_index):
    content_type, user, repo, _ = content_to_index

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
        link_path = path.replace(dest_folder + '/', '').replace('.md', '')

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
        content_type, user, repo, url_prefix = content
        source = repo + ' ' + content_type

        content_getter_f = GET_PAGE_CONTENT[content_type]

        for content in content_getter_f(user, repo, url_prefix):
            markdown_inserter.insert_markdown_doc(source, content['content'], content['title'], content['url'])
            print('Inserted {} file {} | url: {}'.format(content_type, content['title'], content['url']))
