import { encrypt_value } from '@/cryptutil'

describe('encrypt_value', () => {
    const public_key = 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAts0tCjEj+FLJrwzFaFgoeQEAZ8/tWaH2pWM5sisaxmVH/2c32fgMVBQbs5hrr/EpwHLCR+S8W3s908Ne91L+n9QCEJCesDGJRljHrINYxqa8ilhzgQIH33cMvqtvrOWh43bPQUbHVSzNY6/TTsYX9Qn6h5EwV3j02MkgFGF/4yRHuqsMNMTO8o554xzqaoVgV2EAk+GREMtt07RlUXOg e2Ty3VXiJOfHWE7kUYgFhSBtm7AQK3KOHKVsACHBi6z+nIF2uDBeBr26AP5kMab7uQp6M2h/e2VVWwr743UsZoyXEsEchYzBR6RdE32pDVmR84oOlzILj0XcYDCjH/Xq/wIDAQAB'
    it('encrypts values', async () => {
        const result = await encrypt_value(public_key, 'verrah-secret')
        expect(JSON.parse(atob(result))).toEqual(expect.objectContaining({
            key: expect.any(String),
            payload: expect.any(String),
        }))
    })
})

