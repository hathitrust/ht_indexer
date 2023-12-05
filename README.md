# ht_indexer

Application for indexing (add, delete, update) documents in Solr server

This is a FastApi application for indexing XML files in a Solr server

The application runs on http://localhost:8081. The documentation is automatically generated
and you can check it in the http://localhost:8081/docs/.

This application uses the solr server instantiated by to different Solr container for Catalog (solr-sdr-catalog) and
Full-text (solr-lss-dev) search index.
Then, this container must be running before load the API.

## Setting up ht_indexer

1. Clone the repository in your working environment

```git clone git@github.com:hathitrust/ht_indexer.git```

2. Then, go to the folder ``cd ht_indexer``

3. In your workdir, create a sample data. It will generate the folder /sdr1/obj and will download .zip and .mets.xml
   file for a list of records.
   The sample data folder is created in the parent folder of ht_indexer repository. By default, 1% of the documents
   indexed in Catalog image will be added to the sample data.
4. Set up environment variables ```export HT_REPO_HOST=some.host.hathitrust.org```. If you want to add more documents to
   your sample you should define the variable SAMPLE_PERCENTAGE, that represents the percentage of data to retrieve e.g:
   0,5

```./ht_utils/sample_data/sample_data_creator.sh```

## Run the services for retrieving and indexing data

In your workdir, run te scripts belows. They will use the data sample for generating the documents you will want to
index in full-text search index.
This application access to MariaDB database and to Solr, then you should set the following environment variables:

```bash
  export MySQL_USER = mysql_user
  export MySQL_PASS = mysql_pass
```

1. Retrieving data: ```bash run_retriever_processor.sh```
2. Indexing data: ```bash run_retriever_processor.sh```
    3. ```docker compose exec document_indexer python document_indexer_service/document_indexer_service.py --solr_indexing_api http://solr-lss-dev:8983/solr/#/core-x/```

If everything works well, in your browser you will access to the API documentation http://localhost:8081/docs/. You will
also find the indexed documents in http://localhost:8983/solr/#/core-x/query?q=*:*&q.op=OR&indent=true

## Python command to use the services for indexing documents in Full-text search index

``python document_retriever_service/full_text_search_retriever_service.py
--solr_url http://localhost:9033/solr/#/catalog/ --mysql_host mudslide.umdl.umich.edu --mysql_user user_name
--mysql_pass pass --mysql_database ht --query id:hvd.hnr4tg --all_items ``

* If --query parameter is not passed, all the record in Catalog index will be indexed in Full-text search
* By default, only the first item of each record in Catalog are indexed in Full-text search, if --all_items parameter is
  passed, then all the items of the record are added.
    * You can use the command below to index all the item of a specific record
        * `` --solr_url http://localhost:9033/solr/#/catalog/ --mysql_host mudslide.umdl.umich.edu --mysql_user user_name --mysql_pass
          pass --mysql_database ht --query id:012407877 ``

Use the command below to start the service to index documents

``
python document_indexer_service/document_indexer_service.py --solr_indexing_api http://localhost:8983/solr/#/core-x/
``

To run testing locally you would execute `ht_indexer_api_test.py`

Inside the project folder run `python -m pytest` or `pytest`

## [Optional] Data preparation

Create a container with a volume with the documents to process
`docker run -d --rm --name data_creator -v sample_data:/sdr1 alpine tail -f /dev/null`

Use the container to populate the volume with local data
`docker cp ../sample_data/sdr1 data_creator:/sdr1`

Stop the container and the volume will persist
`docker stop data_creator`

## [Optional] How to set up your python environment

On mac,

* Install python
    * You can read this blog to install python in a right way in
      python: https://opensource.com/article/19/5/python-3-default-mac
        * I installed using brew and pyenv
* Install poetry:
    * **Good blog to understand and use poetry
      **: https://blog.networktocode.com/post/upgrade-your-python-project-with-poetry/
    * **Poetry docs**: https://python-poetry.org/docs/dependency-specification/
    * **How to manage Python projects with Poetry
      **: https://www.infoworld.com/article/3527850/how-to-manage-python-projects-with-poetry.html

* Usefull poetry commands (Find more information about commands [here](https://python-poetry.org/docs/cli))
    * Inside the application folder: See the virtual environment used by the application `` poetry env use python ``
    * Activate the virtual environment: ``source ~/ht-indexer-GQmvgxw4-py3.11/bin/activate``, in Mac poetry creates
      their files in the home directory, e.g. /Users/user_name/Library/Caches/pypoetry/..
    * `` poetry export -f requirements.txt --output requirements.txt ``
    * Use `` poetry update `` if you change your .toml file and want to generate a new version the .lock file

## DockerFile explanations

**What is the best python Docker image to use?**
This [post](https://pythonspeed.com/articles/base-image-python-docker-images/)
help to make the decision

We are using the python image **python:3.11-slim-bookworm** as based of our docker.
See this [link](https://hub.docker.com/_/python) to have a look to all the python official Docker images.

The image is based on Debian Bookworm, released June 2023

### Relevant points to decide the image

* Given the speed improvements in 3.11, more important than the base image is making sure you’re on an up-to-date
  release
  of Python.

* The official Docker Python image the absolute latest bugfix version of Python
* It has the absolute latest system packages
* Image system: Debian 12
* Image size: 51MB

The **python:alpine** image was tested and it worked well however I decided to abandon it because it lacks the package
installer
pip and the support for installing wheel packages, which are both needed for installing applications like Pandas and
Numpy. Alpine image is the light one, then we should install several dependencies, e.g. some compiler packages like GCC,
then build the image takes time

## Document generator

Before using this script you should set up the following environment variables

export HOST=something.hathitrust.org
export USER=your_user_name
export PUBLIC_KEY=public_key_name

Reference used for python implementation

Parser XML files
https://lxml.de/tutorial.html#parsing-from-strings-and-files
https://pymotw.com/3/xml.etree.ElementTree/parse.html

MySql
https://www.w3schools.com/python/python_mysql_join.asp

SSH + python script + environment variables to pass user/password
https://www.the-analytics.club/python-ssh-shell-commands/#google_vignette

Pypairtree
https://github.com/unt-libraries/pypairtree/tree/master

Mets fields documentation: https://mets.github.io/METS_Docs/mets_xsd_Attribute_Group_ORDERLABELS.html
Best practices for writing Dockerfiles: https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
Docker reference: https://docs.docker.com/engine/reference/builder/#workdir
Interesting discussion about poetry and docker file:
https://stackoverflow.com/questions/53835198/integrating-python-poetry-with-docker/70161384#70161384
https://github.com/python-poetry/poetry/issues/1178
Poetry & docker good reference: https://github.com/max-pfeiffer/uvicorn-gunicorn-poetry/tree/main/build

Recommended python image: https://pythonspeed.com/articles/base-image-python-docker-images/

* Something I want to test in my Dockerfile: Use poetry for the dependency solver and then use pip for installing the
  final wheel. => Use poetry expert to generate requirements.txt file,
  use this blog as a
  reference: https://medium.com/vantageai/how-to-make-your-python-docker-images-secure-fast-small-b3a6870373a0
* See this video to reduce the size of the container: https://www.youtube.com/watch?v=kx-SeGbkNPU

## Command to use the API

Use this curl command to check if the API is ready to use

``curl --location 'http://localhost:8081/ping/'``

Using this prototype you will be able to index an XML document stored in a data folder inside the server.

Use this curl command to add the XML file

``curl --location --request POST 'http://127.0.0.1:8081/solrIndexing/?path=data%2Fadd' \
--header 'Content-Type: text/plain' \
--data '@'``

Use this curl command to delete the XML file

``curl --location --request POST 'http://127.0.0.1:8081/solrIndexing/?path=data%2Fdelete'``

You can also run the application from your local machine without a docker file using the following command.
However, you will have to set up you python environment.

Use this curl command to query Sorl

``curl http://localhost:9033/solr/catalog/query -d 'json={"query":"ht_id:umn.31951000662660j"}'``

``poetry run python main.py --host 0.0.0.0 --port 8081 --solr_host localhost --solr_port 8983``
