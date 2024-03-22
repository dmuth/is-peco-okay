# PECO Outage Status

## CLI Version

Just a little shell script that I whipped up to pull down the current outage stats from PECO.

It's the same endpoint that their [Official Outage Map](https://secure.peco.com/FaceBook/Pages/outagemap.aspx) uses.

This script can be executed with the following `bash` command:

`bash -c "$(curl -s https://raw.githubusercontent.com/dmuth/peco-outage-status/main/bin/get-peco-outage-status.sh)"`

...and it will return data in this format:

```
{
  "date": "2024-01-10T02:23:18.541Z",
  "outages": [
    {
      "summaryTotalId": "total-1",
      "total_cust_a": {
        "val": 120405
      },
      "total_percent_cust_a": {
        "val": 7.24
      },
      "total_percent_cust_active": {
        "val": 92.76
      },
      "total_cust_s": 1663160,
      "total_outages": 1399
    }
  ]
}
```

I wrote this during [a pretty nasty storm that blew through the area recently](https://www.nbcphiladelphia.com/weather/powerful-storm-expected-to-hit-philly-on-tuesday/3738811/)
as I wanted to get an idea for how many power outages there were without obsessively reloading the page.


## Web Version

...coming soon. :-)  I'm teaching myself [Hugo](https://gohugo.io/) and building a front end
around some web services that I am building.  I will update this README as more work is done.


