---
title: About is PECO Okay?
---

# About Is PECO Okay?

## Is this website official?

**No.**  This website is neither run nor endorsed by PECO.  It is my personal side-project.


## What is this website?

This website displays PECO outage stats across their entire customer base.
It is an alternative to [PECO's Official Status Page](https://www.peco.com/outages/experiencing-an-outage/outage-map). 


## Why was it built?

I found that when a storm comes through and I lose power, I would obsessively refresh [the
PECO status page](https://www.peco.com/outages/experiencing-an-outage/outage-map) on my iPhone, 
to try and get an idea of how many outages they were, and 
how fast the number of outages was going down so that I had an idea of how fast service 
restoration was proceeding.

It certainly... worked.  However, I felt like it was overkill to refresh a page that had a map
on it, and tons and tons of Javascript and CSS.  When I'm without power, the last thing I want to
do is use up my phone's battery even faster.  I just wanted numbers, and to see how they improved 
over time as restoration happened.

And here we are.


## What was the site built in?

I used [Serverless](https://www.serverless.com/) and deployed on Amazon Web Services!

The HTML, Javascript, and CSS are managed with [Hugo](https://gohugo.io/), which is an impressive
static site generator.

The back end consists of AWS Lambda to provide API endpoints, with the underlying code being
written in Python.  The HTML is stored in an S3 bucket and served by via CloudFront which performs
SSL termination.


## Did you really hand code all of the Javascript and CSS?

I did!  If I were building this in the workplace, I would have used jQuery and Bootstrap, because
when you're in the office, your job is to complete things quickly, using the tools at hand,
absent a _really_ good reason to write raw Javascript and CSS.

But this ain't the office, this is a side project.  And it's been awhile since I built something
without using either a Javascript or CSS framework, and I really wanted to craft some straight up
Javascript and CSS.  So I did.


## Is the source code available?

Yep!  You can get the source at [https://github.com/dmuth/peco-outage-status](https://github.com/dmuth/peco-outage-status).


## Have you built anything else?

Yep!  I've built a few things you may find interesting:

- [Diceware Password Generator](https://diceware.dmuth.org/)
- [FastAPI Httpbin](https://httpbin.dmuth.org/) - HTTP endpoints for testing.  Built with FastAPI.
- [Is SEPTA F\*cked?](https://www.isseptafucked.com/) - Like this site.  But for SEPTA. With 100% more profanity.
- [SEPTA Stats](https://septastats.com/) - Stats on Philadelphia Public Transit with 100% less profanity.
- [Splunk Lab](https://github.com/dmuth/splunk-lab) - Stand up a Splunk instance in 30 seconds
- [Tarsplit](https://github.com/dmuth/tarsplit) - Split a tarball on file boundaries
- ...or just [poke around my GitHub](https://github.com/dmuth)


## Get In Touch

If you run into any problems, feel free to [open an issue on GitHub](https://github.com/dmuth/fastapi-httpbin/issues).

Otherwise, you can find me [on the hellscape that is Twitter](https://twitter.com/dmuth),
[Facebook](https://facebook.com/dmuth), 
or drop me an email: **doug.muth AT gmail DOT com**.


