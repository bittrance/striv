import json
import requests


def _endpoint(driver_config, path):
    return '%s/%s' % (driver_config['nomad_url'], path)


def sync_job(driver_config, jid, payload):
    '''
    Create or update a Nomad job. jid will be used as Nomad job id.
    '''
    payload = {'Job': json.loads(payload)}
    payload['Job']['ID'] = jid
    response = requests.post(
        _endpoint(driver_config, 'v1/job/' + jid),
        json=payload
    )
    if response.status_code != requests.codes['ok']:
        raise RuntimeError(response.text)
    return response.json()
