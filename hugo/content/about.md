---
title: About is PECO Okay?
---

# About Is PECO Okay?

## What is PECO?

PECO, also known as the Philadelphia Electric Company, is the energy utility that serves
1.6 million electric customers in the Philadelphia area.


## Is this website official?

**No.**  This website is neither run nor endorsed by PECO.  It is my personal side-project.


## What is this website?

This website displays PECO outage stats across their entire customer base.
It is an alternative to [PECO's Official Status Page](https://www.peco.com/outages/experiencing-an-outage/outage-map). 


## Why was it built?

I found that when a storm comes through and I lose power, I would obsessively refresh [the
PECO status page](https://www.peco.com/outages/experiencing-an-outage/outage-map) on my iPhone.
But here's the thing, I only cared about two numbers:

- How many customers are without power?
- And is that number going up or down?

That's it.  That's all I need to know.  Everything else is extra.  If the number is going **UP**, 
I know things are getting
worse and that it might be awhile before I get power back.  If the number is going **DOWN**, I 
know that restoration is happening, and I can expect power back sonner.

Anything else would just waste my phone's battery, hence my decision to create this lightweight,
text-based website.  [Even my memes are text-based!](/robots.txt)


## What was the site built in?

I used [Serverless](https://www.serverless.com/) and deployed on Amazon Web Services!

The HTML, Javascript, and CSS are managed with [Hugo](https://gohugo.io/), which is an impressive
static site generator.

The back end consists of AWS Lambda to provide API endpoints, with the underlying code being
written in Python.  The HTML is stored in an S3 bucket and served by CloudFront which performs
SSL termination.  The data is stored in DynamoDB.

For deplying APIs, Serverless is GREAT!  For DynamoDB tables, [it is a mixed bag](https://github.com/dmuth/is-peco-okay/blob/7f2f3af88c7ac40a14c63d3f9bcd021b2e58cff6/serverless.yml#L120).  I do NOT
recommend Serverless for Cloudfront distributions.


## Did you really hand code all of the Javascript and CSS?

I did!  If I were building this in the workplace, I would have used jQuery and Bootstrap, because
when you're in the office, your job is to complete things quickly, using the tools at hand,
absent a _really_ good reason to do it in a way that will take longer.

But this ain't the office, this is a side project.  And it's been awhile since I built something
without using either a Javascript or CSS framework, and I really wanted to craft some straight up
Javascript and CSS.  So I did.


## If everything is hand-coded, why did you use Chart.js for the graph?

Because if I wanted to mess with individual pixels I'd go back to the 3rd Grade, write some 
[Logo](https://en.wikipedia.org/wiki/Logo_(programming_language)), and then have chocolate milk 
at lunch while eating hamburger hash with a spork.

...or you could just let me use Chart.js like an adult.


## How the HECK did you get a default index.html working in a CloudFront Distribution?

I used a Lambda@Edge function to add `index.html` as described [on this page](https://aws.amazon.com/blogs/networking-and-content-delivery/implementing-default-directory-indexes-in-amazon-s3-backed-amazon-cloudfront-origins-using-cloudfront-functions/).  

It would be *really cool* if that functionality was built into CloudFront, Amazon.  Come on, Amazon, I know you can do it.  I believe in you.


## Is PECO Aware of this website?

[They are now!](https://technical.ly/software-development/is-peco-okay-power-outage-tracker-doug-muth-septa/)  PECO's leadership hasn't complained to me or sent me any legal threats, and I take that to be a good sign.  If nothing else, I hope the site brightened their day a little.


## Is the source code available?

Yep!  You can get the source at [https://github.com/dmuth/is-peco-okay](https://github.com/dmuth/is-peco-okay).


## Are there any other websites like this one?

Yes!  There is [https://poweroutage.us/](https://poweroutage.us/) which keeps track of power outages
across the entire United States.


## Have you built anything else?

Yep!  I've built a few things you may find interesting:

- [Diceware Password Generator](https://diceware.dmuth.org/) - Passphrase generator using the "diceware" method.
- [Dead Simple QR Code Generator](https://httpbin.dmuth.org/qrcode/) - No ads, signups, or spam. Just QR Codes when you want them.
- [FastAPI Httpbin](https://httpbin.dmuth.org/) - HTTP endpoints for testing.  Built with FastAPI.
- [Is SEPTA F\*cked?](https://www.isseptafucked.com/) - Like this site.  But for SEPTA. With 100% more profanity.
- [SEPTA Stats](https://septastats.com/) - Stats on Philadelphia Public Transit with 100% less profanity.
- [Splunk Lab](https://github.com/dmuth/splunk-lab) - Stand up a Splunk instance in 30 seconds.
- [Tarsplit](https://github.com/dmuth/tarsplit) - Split a tarball on file boundaries.
- [Grafana Network Monitor](https://github.com/dmuth/grafana-network-monitor) - A quick and dirty collection of scripts and dashboards I built to monitor my home's Internet connectivity by pinging multiple hosts on the Internet.
- ...or just [poke around my GitHub](https://github.com/dmuth)


## Got any press coverage?

[Technical.ly did a nice writeup on this site in Jun, 2024.](https://technical.ly/software-development/is-peco-okay-power-outage-tracker-doug-muth-septa/)

If you wanna interview me for a story on this site, feel free to reach out!


## Get In Touch

If you run into any problems, feel free to [open an issue on GitHub](https://github.com/dmuth/fastapi-httpbin/issues).

Otherwise, you can find me [on the hellscape that is Twitter](https://twitter.com/dmuth),
[Facebook](https://facebook.com/dmuth), 
or drop me an email: **doug.muth AT gmail DOT com**.

{{< bottom-padding >}}

