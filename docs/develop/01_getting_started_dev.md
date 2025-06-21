
# Getting started developing

## Setup your project development environment

Getting started on developing your own project based on this template

> **DO NOT FORK** this is meant to be used from **[Use this template](https://github.com/pamagister/gpx-kml-converter/generate)** feature.

1. Click on **[Use this template](https://github.com/pamagister/gpx-kml-converter/generate)**
3. Give a name to your project  
   (e.g. `my_python_project` recommendation is to use all lowercase and underscores separation for repo names.)
3. Wait until the first run of CI finishes  
   (Github Actions will process the template and commit to your new repo)

## Troubleshooting

### Problems with release pipeline

If you get this error below:
```bash
/home/runner/work/_temp/xxxx_xxx.sh: line 1: .github/release_message.sh: Permission denied
```

You have to run these commands in your IDE Terminal or the git bash and then push the changes.
```bash
git update-index --chmod=+x ./.github/release_message.sh
```

