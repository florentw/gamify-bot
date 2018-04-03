[//]: # "Documentation generated for version 1.0"


# Gamify Bot

[![Build status](https://travis-ci.org/florentw/gamify-bot.svg?branch=master)](https://travis-ci.org/florentw/gamify-bot)
[![Test Coverage](https://api.codeclimate.com/v1/badges/03b56167306baeca919d/test_coverage)](https://codeclimate.com/github/florentw/gamify-bot/test_coverage)
[![Maintainability](https://api.codeclimate.com/v1/badges/03b56167306baeca919d/maintainability)](https://codeclimate.com/github/florentw/gamify-bot/maintainability)

**GamifyBot** is a [Slack](https://slack.com/) **chat bot** written in [Python](https://www.python.org/) to gamify shared team tasks assignement in agile teams.

All development teams have **routine tasks** that need to be **shared among team members**, for instance:
- Analysis of support issues before inserting them in the team's backlog
- Performing routine merges or backports
- Fixing quality gates on the team's master branch
- Etc.

Experience has shown that **team members are reluctant to perform those tasks**, perceived as having a low value, low visibility (a.k.a *boring*), and usually a few team mates are taking ownership of most of these routine tasks.

In order to **bring back fun to these routine tasks**, and to **even out the load on the team**, we decided to experiment with gamification, and the idea of **GamifyBot** was born during a team retrospective!

| High Scores                                                    |  Tasks list
|----------------------------------------------------------------|---------------------------------------------------
| ![Gamify scores](./docs/img/gamify_scores.png "Gamify scores") | ![Gamify tasks](./docs/img/gamify_tasks.png "Gamify tasks")

## Game rules

If you are looking for a **user guide**, please refer to the following document: [Game rules](docs/game-rules.md).

## Running the bot with python on Linux

You will need Python 2.7 and `pip` installed, then you can use `virtualenv` to create an environment for your instance.

At the root of the project directory, run:

```bash
# Install virtualenv
sudo pip install virtualenv

# Creates the environment
virtualenv --python=/usr/bin/python2.7 env

# Activate the environment
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Then you need to provide your *Slack bot token* (please refer to [Slack's documentation](https://api.slack.com/bot-users))

And you are now ready to run the bot:

```bash
# Export your slack bot token to be passed to the bot
export SLACK_BOT_TOKEN=xoxb-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

python gamifybot.py
-> GamifyBot connected and running!
```

## Running the bot from Docker

You can use [Docker](https://www.docker.com/) to run the GamifyBot, it is very easy.

At the root of the project directory, start by building the Docker image:

```bash
docker build -t gamify-bot .

[...]

Successfully built 3e8b92135d28
Successfully tagged gamify-bot:latest
```

Then you need to provide your *Slack bot token* (please refer to [Slack's documentation](https://api.slack.com/bot-users))
and run the container from the freshly built image:

```bash
export SLACK_BOT_TOKEN=xoxb-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

docker run -it --rm -e SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN --name gamify-bot-replica gamify-bot
-> GamifyBot connected and running!
```

**Warning**: Keep your `SLACK_BOT_TOKEN` secret, do not pass the value directly as argument to the command.

## License

GamifyBot is licensed under the liberal [MIT License](./LICENSE).

## Contribution

Pull requests are more than welcome!
