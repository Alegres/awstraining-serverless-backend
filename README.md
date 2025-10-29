# README
## Prerequisites
* Python & Pip
* Virtualenv Manager
* Node Package Manager
* CDK
* AWS CLI
* [PROFILE] with credentials related to your Sandbox Technical User created in ```C:\Users\[CORPID]\.aws\credentials``` 

**Instruction:**
* https://docs.aws.amazon.com/cdk/v2/guide/work-with-cdk-python.html

Ensure pip & virtualenv are installed:
```bash
python -m ensurepip --upgrade
python -m pip install --upgrade pip
python -m pip install --upgrade virtualenv
```

Install CDK:
```bash
npm install -g aws-cdk@2.1006.0
```

## Setup CDK project
Create an empty directory and go there:
```bash
mkdir app
cd app
```

Initialize CDK (we will use Python):
```bash
cdk init app --language python
```

Activate project's virtual environment:
```bash
source .venv/Scripts/activate
```

Install required Python's dependencies:
```bash
python -m pip install -r requirements.txt
```

Make sure that you ```C:\Users\[CORPID]\.aws\config``` file has the correct region set (we should work in **eu-central-1**):
```
[default]
region = eu-central-1
output = json
```

You can also export **AWS_REGION:**
```bash
export AWS_REGION=eu-central-1
```

Bootstrap CDK to your account:
```bash
cdk bootstrap --profile [PROFILE]
```

Run synthesis:
```bash
cdk synth
```

Deploy the infrastructure:
```
cdk deploy --profile [PROFILE]
```

## Common Issues
If you face the following error:
```bash
$ cdk synth
Traceback (most recent call last):
  File "C:\personal\awstraining-serverless\basic-backend\app\app.py", line 4, in <module>
    import aws_cdk as cdk
ModuleNotFoundError: No module named 'aws_cdk'
Subprocess exited with error 1
```

make sure that you activated your env:
```bash
source .venv/Scripts/activate
```

Also, when running **cdk** commands, make sure to stay at the location where your **cdk.json** file is present.

# 🛠️ Deploying Python CDK Stacks to Multiple Environments Using YAML Configs

This guide shows how to deploy your **AWS CDK (Python)** stack to **multiple environments** (like `dev`, `test`, `prod`) using:

- Named **AWS profiles**
- Environment-specific **YAML configuration files**
- Clean **Python CDK app logic**

---

## 📁 Folder Structure

```
cdk/
├── app.py
├── stack.py
├── config/
│   ├── dev.yaml
│   ├── test.yaml
│   └── prod.yaml
```

---

## 🧾 Example: `config/dev.yaml`

```yaml
aws_profile: dev-profile
region: eu-central-1
account: 123456789012
env_name: dev
app_name: my-app-dev
```

---

## 🐍 `app.py` — Load YAML Configs Dynamically

```python
import yaml
import sys
from aws_cdk import core as cdk
from stack import MyStack

def load_config(env_name):
    with open(f"config/{env_name}.yaml", "r") as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python app.py <env>")
        sys.exit(1)

    env_name = sys.argv[1]
    config = load_config(env_name)

    # Activate the correct AWS profile
    import os
    os.environ["AWS_PROFILE"] = config["aws_profile"]

    app = cdk.App()

    MyStack(
        app, 
        f"{config['app_name']}-stack",
        env=cdk.Environment(account=config["account"], region=config["region"]),
        config=config  # optional: pass whole config to the stack
    )

    app.synth()
```

---

## 📦 `stack.py` — Use the Config in Your Stack

```python
from aws_cdk import core as cdk
from aws_cdk import aws_s3 as s3

class MyStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, id: str, config: dict, **kwargs):
        super().__init__(scope, id, **kwargs)

        bucket_name = f"{config['app_name']}-bucket"
        s3.Bucket(self, "MyBucket", bucket_name=bucket_name)
```

---

## 🚀 Deploy Commands

```bash
# Deploy to dev environment
python app.py dev
cdk deploy

# Deploy to prod environment
python app.py prod
cdk deploy
```

---

## 💡 Tips

- You can also use `cdk deploy --profile XYZ` if you prefer CLI-level profile control.
- The YAML config can include additional values like tags, feature flags, resource names, etc.
- If you have multiple stacks, you can load and deploy them conditionally based on the config.


# Welcome to your CDK Python project!

This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
