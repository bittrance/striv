{
  dimensions: {
    maturity: {
      priority: 1,
      values: {
        accept: {
          params: {
            debug: true,
            command: 'echo Hello'
          }
        },
        operational: {
          params: {
            debug: false,
            command: 'echo Bye'
          }
        }
      }
    },
    period: {
      priority: 1,
      values: {
        daily: {
          params: {
            debug: false
          } 
        }
      }
    }
  },
  executions: {
    'local_nomad': {
      name: 'Dev Nomad',
      driver: 'nomad',
      logstore: 'nomad',
      driver_config: {
        nomad_url: 'http://localhost:4646'
      },
      default_params: {
        debug: true
      },
      payload_template: importstr 'nomad_template.jsonnet'
    },
    'periodic_nomad': {
      name: 'Periodic Nomad',
      driver: 'nomad',
      logstore: 'nomad',
      driver_config: {
        nomad_url: 'http://localhost:4646'
      },
      default_params: { },
      payload_template: importstr 'nomad_periodic.jsonnet'
    }
  }
}