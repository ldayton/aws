#---- PROVIDE AWS KEYS ----#

# export AWS_ACCESS_KEY_ID='???'
# export AWS_SECRET_ACCESS_KEY='???'

#---- PROVIDE SOME DEFAULTS ----#

# export AWS_DEFAULT_REGION='us-west-1'
# export AWS_DEFAULT_VPC='???'
# export AWS_DEFAULT_SUBNET='???'
# export AWS_DEFAULT_SECURITY_GROUPS='???'
# export AWS_DEFAULT_AMI='ami-4826c22b' # Centos 7
# export AWS_DEFAULT_KEY_NAME='???'
# export AWS_DEFAULT_INSTANCE_TYPE='???'
# export AWS_DEFAULT_OUTPUT='json'


#----- USEFUL FUNCTIONS TO SOURCE IN YOUR BASH PROFILE ----#

# print info on latest ubuntu ami
function latestubuntu() {
	docker run --rm --env-file <(env | grep AWS_) aws latest-ubuntu "$@" | jq .
}

# print info on latest centos ami
function latestcentos() {
	docker run --rm --env-file <(env | grep AWS_) aws latest-centos "$@" | jq .
}

# create an AWS instance with the given name
function mkinstance() {
	docker run --rm --env-file <(env | grep AWS_) aws create-instance "$@" | jq .
}

# terminate instance with provided id
function killinstance() {
	docker run --rm --env-file <(env | grep AWS_) aws kill-instance "$@" | jq .
}

# stop instance with provided id
function stopinstance() {
	docker run --rm --env-file <(env | grep AWS_) aws stop-instance "$@" | jq .
}

function killinstances() {
  for id in "$@"; do killinstance $id; done
}

function stopinstances() {
  for id in "$@"; do stopinstance $id; done
}

# start instance with provided id
function startinstance() {
	docker run --rm --env-file <(env | grep AWS_) aws start-instance "$@" | jq .
}

# reboot instance with provided id
function rebootinstance() {
	docker run --rm --env-file <(env | grep AWS_) aws reboot-instance "$@" | jq .
}

# list all AWS instances
function listinstances() {
	docker run --rm --env-file <(env | grep AWS_) aws list-instances "$@" | jq .
}

# given a name, and possibly some options, create an AWS instance and ssh into it
function sshinstance() {
  JSON=$(mkinstance --wait "$@")
	echo $JSON | jq .
	IP=$(echo $JSON | jq -r .PublicIp)
	echo
	sshu $IP centos
}

# given a host dns or ip, ssh's into it with the provided username, retrying until success
function sshu() {
  if [ "$#" -ne 2 ]; then
    echo "Usage: sshu (host) (username)"
    return 1
  fi
  HOST="${1}"
  USERNAME="${2}"
  while :
  do
    if ssh -o ConnectTimeout=1 -o StrictHostKeyChecking=no "${USERNAME}@${HOST}" 2> /dev/null; then
      return
    else
      echo 'waiting for ssh to become available ...'
      sleep 3
    fi
  done
}
