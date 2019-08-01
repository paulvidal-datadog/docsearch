# Docsearch

## Install ES using docker

```bash
docker pull docker.elastic.co/elasticsearch/elasticsearch:7.2.0
```

## Launch ES using docker 

```bash
docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.2.0
```

## ES

### Get indices

```bash
 curl -X GET 'localhost:9200/_cat/indices?v'
```

### List documents

```bash
curl -XPOST -H 'Content-Type: application/json' 'localhost:9200/documentation/_search?pretty'
```

## Virtual env 

```bash
 source venv/bin/activate
```