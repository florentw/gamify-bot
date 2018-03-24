# Gamify Bot

The **GamifyBot** is a [Slack](https://slack.com/) **chat bot** written in [Python](https://www.python.org/) to gamify shared team tasks assignement in agile teams.

All development teams have **routine tasks** that need to be **shared among team members**, for instance:
- Analysis of support issues before inserting them in the team's backlog
- Performing routine merges or backports
- Fixing quality gates on the team's master branch
- Etc.

Experience has shown that **team members are reluctant to perform those tasks**, perceived as having a low value, low visibility (a.k.a *boring*), and usually a few team mates are taking ownership of most of these routine tasks.

In order to **bring back fun to these routine tasks**, and to **even out the load on the team**, we decided to experiment with gamification, and the idea of **GamifyBot** was born during a team retrospective!

![Gamify scores](./docs/img/gamify_scores.png "Gamify scores")

## Game rules

Please refer to the following document for game rules: [Game rules](docs/game-rules.md).

## Running the bot from Docker

You can use [Docker](https://www.docker.com/) to run the GamifyBot, it is very easy.

At the root of the project directory, start by building the Docker image:

```
$ docker build -t gamify-bot .

[...]

Successfully built 3e8b92135d28
Successfully tagged gamify-bot:latest
```

Then you need to provide your *Slack bot token* (please refer to [Slack's documentation](https://api.slack.com/bot-users))
and run the container from the freshly built image:

```
$ export SLACK_BOT_TOKEN=xoxb-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

$ docker run -it --rm -e SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN --name gamify-bot-replica gamify-bot
GamifyBot connected and running!
```

**Warning**: Keep your `SLACK_BOT_TOKEN` secret, do not pass the value directly as argument to the command.

## License

GamifyBot is licensed under the liberal [MIT License](./LICENSE).

## Contribution

Pull requests are more than welcome!

