# option-history

Here we back test a very simple stock option strategy.
We fetch historic data using [Polygon.io](https://polygon.io/) API.

## Setup
We need Python 3.10 or newer.

To run the code we need to create an [API key](https://polygon.io/dashboard/api-keys) on their site.
Then we have to export it so the script can access it.
```sh
export POLYGON_API_KEY=<api-key>
```

Note that the script makes lots of requests to the **options** API, so it will quickly exceed the limit of 5 calls/minute of the _Basic_ plan.
The _Starter_ plan should be sufficient.
