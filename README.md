# Docsearch

## Setting up ES

### Install ES using docker

```bash
docker pull docker.elastic.co/elasticsearch/elasticsearch:7.2.0
```

### Launch ES using docker 

```bash
docker run -d -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.2.0
```

### Get indices

```bash
 curl -X GET 'localhost:9200/_cat/indices?v'
```

### List documents

```bash
curl -XPOST -H 'Content-Type: application/json' 'localhost:9200/documentation/_search?pretty'
```

## Setting up Virtual env 

### Create

```bash
python3 -m venv ./venv
```

### Activate

```bash
source venv/bin/activate
```

## Running the scraper and the server

### Scraper

This will delete the ES indice `documentation`, create a new one and re-index everything (will cause some downtime)

```bash
python scraper.py
```

### Server

#### DEV

In development, run

```bash
FLASK_ENV=development python server.py
```

and in another tab, start the vue dev server for hot reloading (they will proxy all call with `/api` to the flask server
as specified in `search/vue.config.js` devServer section)

```bash
yarn --cwd search serve 
```

#### PROD

In production, only run the flask web server using guinicorn (the server will itself serve the static assets as opposed to a 
devServer like in development). 

```bash
gunicorn --bind 0.0.0.0:5000 wsgi:app
``` 

You will need to have beforehand built the static assets by running:

```bash
yarn --cwd search build
``` 

## Deploying in production

### 1. Build the docker image locally

There are no pipelines so you will have to build the image locally and send it to ECR.

Get the latest tag and **increment it**.

```
latest-image --cloud aws staging docsearch
```

Then add this tag to the following line

```bash
docker build -t 727006795293.dkr.ecr.us-east-1.amazonaws.com/docsearch:<tag> .
```

### 2. Login to the registry

```bash
aws-vault exec staging-engineering -- aws ecr get-login --region us-east-1 --no-include-email --registry-ids 727006795293
```

### 3. Send the image to the registry

We send the image to the us1.staging ECR registry directly

```bash
docker push 727006795293.dkr.ecr.us-east-1.amazonaws.com/docsearch:<tag>
```

### 4. Update the helm chart

Go to `/k8s-resources`, in the `k8s/docsearch` folder and update the `values.yaml`.

```
image_web:
  name: 727006795293.dkr.ecr.us-east-1.amazonaws.com/docsearch
  tag: <tag>
```

### 5. Push a PR, merge it and then pull locally `k8s-resources`

### 6. Apply the new chart

Once the image is sent to the us1.staging ECR repository, deploy everything using the chart in k8s. Fot his go to 
`k8s-resources` repository and run:

```bash
kubectx general1.us1.staging.dog  # make sure to be in the right cluster and namespace 
kubens datadog
k template apply docsearch
```

## Add a url in the proxy

The first time the project is deployed, update the internal proxy.

You will then need to redeploy the internal services proxy on us1.staging, which currently lives on the chinook cluster in the sre namespace (this might change in the future)

```bash
kubectx chinook.us1.staging.dog  # make sure to be in the right cluster and namespace
kubens sre
k template apply internal-services-proxy
``` 
