# striv - simple batch job operation

* **striv is still under construction. In particular, it is not yet properly packaged. Examples in this README are typically formulated as if striv was available from Docker Hub. Proceed with caution!** 

striv promises simple and devops-friendly batch job operation on top of Hashicorp Nomad. It has a simple web interface and exposes a rich REST API for automation. It provides great freedom in templating job definitions, while also making it easy for non-developers to configure, schedule and operate jobs.

## Getting started

The easiest way to get started is using the included Docker Compose file:
```
wget https://raw.githubusercontent.com/bittrance/striv/master/examples/getting-started/docker-compose.yml
docker-compose -p striv up
```
This will start a striv, postgresql, nomad and supporting services on the latest released version of striv. Nomad will mount your Docker socket so as to be able to run containers. striv is available on http://localhost:8080, with no authentication. **This setup contains hard-coded credentials and a Nomad, do don't run it in production!**

Let's start a template from scratch. First we need an execution. Let's create a state file called `hello-world.jsonnet`:
```jsonnet
{
  executions: {
    hello_world: {
      name: 'Hello World',
      // We are talking to a Nomad cluster
      driver: 'nomad',
      logstore: 'nomad',
      driver_config: {
        // since both striv and nomad are in the same Docker Compose file, striv can use the service name to refer to Nomad.
        nomad_url: 'http://nomad:4646'
      },
      // The actual template is a jsonnet snippet stored as a JSON string. We could write it inline, but it would be hard to read, particularly as JSON has no multi-line strings. Instead, we import it from a separate file.
      payload_template: importstr './nomad_job.jsonnet',
      // These are default values for the params in your template
      default_params: {
        greeting: 'World'
      }
    }
  }
}
```
Now we need to create the actual template `nomad_job.jsonnet`. This is an ordinary [Nomad Job description](https://www.nomadproject.io/api-docs/json-jobs#syntax), but expressed in jsonnet. This allows us to parameterize the greeting (the top-level { "Job": {...}} is handled by the driver):
```jsonnet
{
  Type: 'batch',
  Name: 'greeter',
  Datacenters: ['dc1'],
  Periodic: {
    // Run this job every minute.
    Spec: "*/1 * * * * *",
  },
  TaskGroups: [
    {
      Count: 1,
      Name: 'greeter',
      Tasks: [
        {
          Config: {
            image: 'alpine:latest',
            command: '/bin/sh',
            // This will be expanded before the Nomad API call is made.
            args: ['-c', 'echo Hello ' + params.greeting],
          },
          Driver: 'docker',
          Name: 'greeter',
          Resources: {
            CPU: 500,
            MemoryMB: 256
          }
        }
      ]
    }
  ],
}
```
We can now load this state file into striv. This replaces all your existing executions, and there is currently no validation against existing jobs, so please make sure you are addressing the right striv.

```bash
docker run -v $PWD:/getting-started --network striv bittrance/striv-tools /striv/cli.py --striv-url http://striv:8080 load-state /getting-started/hello-world.jsonnet
```
We can now open a browser and create a new job.

![New Job View](docs/images/new-job.png)

If you wait a minute, Nomad will have run the job, and we can inspect the log file. (The UI does not currently refresh, so you may want to ctrl+r.)

![Successful Run View](docs/images/successful-run.png)

Our greeting service works well on Earth, but market research indicates that it does not go down so well on other celestial bodies. We can use a dimension to allow choosing different, pre-defined greeting phrases. Extend `hello-world.jsonnet` with a dimension definition:

```jsonnet
{
  executions: {
    // Same as above
  },
  dimensions: {
    audience: {
      priority: 1,
      values: {
        world: {
          params: {
            greeting: 'Terra'
          }
        },
        moon: {
          params: {
            greeting: 'Luna'
          }
        }
      }
    }
  }
}
```
We reload the state:
```bash
docker run -v $PWD:/getting-started --network striv bittrance/striv-tools /striv/cli.py --striv-url http://striv:8080 load-state /getting-started/hello-world.jsonnet
```
We can update the job in the browser to add the job to the "greeting" dimension.

![Modify Job to dimension](docs/images/modify-job-with-dimensions.png)

A few minutes later, we can inspect the log file of the latest run.

![Successful run with dimension](docs/images/run-with-dimension.png)

Neat, eh?

## Rationale

striv is a master data system for containerized batch jobs running on Nomad (support for Kubernetes and Fargate is planned). striv was written for organisations that run large numbers of batch jobs on behalf of customers (importing or exporting data, reporting, et c, often referred to as "integrations"). Such jobs tend regularly to get mugged by reality and when you have many of them, making sure they do their thing is a job best done by people who are close to the customer.

striv allows splitting the responsibility for operating the infrastructure from operating the batch jobs themselves. The assumption behind striv is that developers or operations maintain job templates, while support or customer care set up, maintain and to some extent operate jobs. Thus, job descriptions are jsonnet templates while job configuration and operation can be performed via web UI.

striv leverages your orchestration system's native ability to run periodic ("cron") jobs, which means that striv itself need not impact your availability. Should you want to leverage striv REST APIs from your production environment, striv can be run in a resilient multi-node configuration.

## Core concepts

### State

**execution**: An execution represents a job template for a particular target orchestration system (e.g. one Nomad cluster). The actual template is a jsonnet script and can thus be arbitrarily advanced. For example, sections can be conditional and values can be calculated from multiple parameters. The exact scope of a template depends on your containers. If you have managed to standardize your container invocation, you may get away with a single template. If you mount filesystems and require side cars, you probably need to have many templates and you may want to modularize your jsonnet. If you need manytemplates, you can use jsonnet functions to modularize your templates.

**dimension**: A dimension represents some differentiator that can be used to categorize jobs. Typical dimensions might be customer, product and datacenter. A dimension has a list of possible values, each of which has its own key-value map of parameters. For example, you could have a `service_level` dimension with values "enterprise", "basic" and "free" each of which has parameters for scheduling priority and alerting strategy.

### Batch Jobs

**job**: A job represents a job/service/task in one of the supported oechestration systems. A job is configured by linking it to one or more dimension values. Each value comes with a parameter map. When creating a job, all the job's parameter maps are merged to create a single parameter map which is then used to instantiate the template. The job can also override values.

**run**: A run represents a single execution of a job. For most jobs, striv will automatically detect when the job has been executed by the orchestration system. If the job template supports it, it is also possible to perform a manual run (e.g. rerun the job).

### Separation of responsibility

In a typical setup, executions and dimensions are maintained in a Git repository. When a branch is merged to master, your CI/CD pipeline updates striv. Executions and dimensions can be expressed in jsonnet for flexibility and modularity. For simple scenarios, jobs are created manually using the web ui. For more advanced setups, jobs can be maintained programmatically via the REST API from some other source, e.g. a CRM system.

## Configuring

 * Store [required]: Where striv stores its state
 * Log source [optional]: Striv can display job logs, which can be very useful for debugging
 * Archive [optional]: Striv can be instructed to archive logs for itself. This is useful when you don't have a centralized log aggregation platform.

### Store

striv supports several different stores. Stores are configured using the `--store-config` parameter, which takes a JSON string as argument.

#### sqlite

sqlite is the default store, making it easy to start an instance for testing. The sqlite driver is not recommended for production installation (particularly not in multi-node configurstions) because of its performance characteristics.

- type: sqlite
- database: file name of the sqlite file. This defaults to `$TMP/striv.db`.

#### mysql and postgres

Standard RDBM parameters:

- type: "mysql" or "postgres"
- host: 
- port:
- user:
- password:
- database (mysql) or dbname (postgres):

Example JSON for connecting to mysql:

```json
--store-config '{
  "type": "mysql",
  "host": "127.0.0.1",
  "user": "striv",
  "password": "verrah-secret",
  "database": "striv"
}'
```

The deserialized JSON is passed directly to the Python DB Api `connect` method for the respective driver, so you can pass any driver-specific parameters in the JSON, e.g. parameters for TLS connections.

### Secrets

striv supports encrypting secrets natively, both through the web UI and in the templates. Secrets are stored and passed around encrypted, but are passed in cleartext to the backend. Given that it is almost impossible to stop a determined attacker from abusing the configuration to exfiltrate this cleartext, striv secrets support should primarily be considered obfuscation. If you want real security, your jobs should integrate directly with a secrets management service such aa Hashicorp Vault or AWS KMS. In this scenario, you encrypt the secret yourself and add it to striv as a text property.

In order to activate native secrets support, you generate a 2048-bit, PEM-encoded PKCS8 RSA key like so:
```bash
striv-cli generate-key
```
If you lose this key, you will not be able to recover your secrets, so please make proper backups.

This key is then passed to striv like so:

```bash
--encryption-key '-----BEGIN PRIVATE KEY-----
...
-----END PRIVATE KEY-----
```

If you activate secrets support, you can also store execution and dimension values encrypted, enabling tracking this configuration in your VCS.

```bash
echo 'verrah-secret' | striv-cli encrypt-value
```
This can then be inserted into your executions and dimensions:
```jsonnet
{
  dimensions: {
    environment: {
      production: {
        values: {
          mysql_password: {
            type: "secret",
            encrypted: "..."
          }
...
```

### Archiving logs

Nomad will only retain logs for a limited time, so if you want to be able to inspect log files for historic jobs, striv will need to archive them.

When you activate the archiver, every time a run's logs are requested, the API will automatically archive those logs. The refresh job can use this fact to request logs from all runs that are completed, creating a complete archive of run logs.

The following stores are available:

**file**: a directory, presumably a mounted file system.

**s3**: an Amazon S3 bucket.

```json
--archive-config '{
  "type": "file",
  "archive_dir": "/tmp"
}'
```
Striv will not prune archived logs for you; you will need to set up an administrative routine to remove sufficiently old logs.
striv-cli encrypt-value
```
This can then be inserted into your executions and dimensions:
```jsonnet
{
  dimensions: {
    environment: {
      production: {
        values: {
          mysql_password: {
            type: "secret",
            encrypted: "..."
          