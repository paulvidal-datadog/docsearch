import os
import shutil

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
    ('wiki', 'Datadog', 'logs-backend', 'wiki')
}


# For crawling wiki in repos
def get_all_wiki_page_content(user, repo, url_prefix):
    dest_folder = "./{}_{}_wiki".format(user, repo)

    clone_wiki_content(user, repo, dest_folder)

    for path in get_all_files_path(dest_folder):
        file = open(path, "r")
        link_path = path.replace(dest_folder + '/', '').replace('.md', '')

        yield {
            'title': link_path.replace('-', ' '),
            'url': WIKI_URL.format(user, repo, url_prefix, link_path),
            'content': file.read()
        }


def clone_wiki_content(user, repo, dest_folder):
    # clear the dest directory if it exists
    shutil.rmtree(dest_folder, ignore_errors=True)

    repo = GIT_WIKI_URL.format(user, repo)
    print('Cloning wiki {} into folder {} ...'.format(repo, dest_folder))
    Repo.clone_from(repo, dest_folder)
    print('Cloning successful!')


# For crawling repos
def get_all_repo_page_content(user, repo, url_prefix):
    dest_folder = "./{}_{}_repo".format(user, repo)

    clone_repo_content(user, repo, dest_folder)

    for path in get_all_files_path(dest_folder):
        file = open(path, "r")
        link_path = path.replace(dest_folder + '/', '')

        yield {
            'title': link_path,
            'url': URL.format(user, repo, url_prefix, link_path),
            'content': file.read()
        }


def clone_repo_content(user, repo, dest_folder):
    # clear the dest directory if it exists
    shutil.rmtree(dest_folder, ignore_errors=True)

    repo = GIT_URL.format(user, repo)
    print('Cloning repository {} into folder {} ...'.format(repo, dest_folder))
    Repo.clone_from(repo, dest_folder)
    print('Cloning successful!')


def get_all_files_path(path):
    files = []

    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            if not file.startswith('_') and file.endswith('.md'):
                files.append(os.path.join(r, file))

    return files


if __name__ == '__main__':
    import es

    es.delete()
    es.create()

    # for wiki in get_all_wiki_page_content('junegunn', 'fzf'):
    #     markdown_inserter.insert_markdown_doc('junegunn', wiki['content'], wiki['title'], wiki['url'])

    for content in CONTENT_TO_INDEX:
        content_type, user, repo, url_prefix = content
        source = repo + ' ' + content_type

        if content_type == 'wiki':
            for wiki in get_all_wiki_page_content(user, repo, url_prefix):
                markdown_inserter.insert_markdown_doc(source, wiki['content'], wiki['title'], wiki['url'])
                print('Inserted wiki file {} | url: {}'.format(wiki['title'], wiki['url']))

        elif content_type == 'repo':
            for repo in get_all_repo_page_content(user, repo, url_prefix):
                markdown_inserter.insert_markdown_doc(source, repo['content'], repo['title'], repo['url'])
                print('Inserted repo file {} | url: {}'.format(repo['title'], repo['url']))
