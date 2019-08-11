FROM python:3

WORKDIR /usr/src

COPY . /usr/src

# Build backend dependencies
RUN pip install -r requirements.txt

# Install YARN
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt-get -y update && apt-get -y install yarn

# Install frontend dependencies
RUN yarn --cwd search install

# Build frontend static files
RUN yarn --cwd search build