# Vector Talent Insights — RSS Feed

An automatically updated RSS feed for [Vector Talent Insights](https://www.vectorta.com/insights).

## Subscribe

Add this URL to your RSS reader:

```
https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/vector-talent-insights.xml
```

## How it works

A GitHub Action runs daily at 08:00 UTC. It scrapes the Vector Talent Insights page, regenerates the XML feed, and commits any changes back to this repository. If there are no new articles, nothing is committed.

## Manual update

Go to **Actions > Update RSS Feed > Run workflow** to trigger an update at any time.
