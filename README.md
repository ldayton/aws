# aws

AWS utilities

## Setup

- Expose these environment variables
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_DEFAULT_REGION` (e.g., `us-west-1`)
  - `AWS_DEFAULT_SUBNET` (e.g., `subnet-xxxxxxxx`)
  - `AWS_DEFAULT_SECURITY_GROUPS` (e.g., `group1,group2`)
  - `AWS_DEFAULT_KEY_NAME` (e.g. `mykey`)
  - `AWS_DEFAULT_AMI` (e.g., `ami-6e1a0117`)
  - `AWS_DEFAULT_INSTACE_TYPE` (e.g., `m5.xlarge`)

## Run with Docker

- Build the container:

      $ cd aws/
      $ docker build -t aws .

- Run the container:

      $ docker run --rm --env-file <(env | grep AWS_) aws

## Run with Virtualenv

- Install virtualenv:

        $ pip3 install virtualenv

- Create a virtualenv if you don't have one:

        $ virtualenv ~/venv

- Activate your virtualenv:

        $ source ~/venv/bin/activate

- Install the requirements:

        (venv) $ pip install -r requirements.txt

- Run the script:

        (venv) $ ./aws.py

## Useful bash functions

- Fill out the default values in `functions.bash`, unless you already exported them above in your shell.
- Source `functions.bash` in this directory.
- Don't forget to build the aws container as above.
