import { compactDateTime } from '@/formatting.js'

describe('compactDateTime', () => {
    const now = new Date('2020-11-04T18:21:09.731+0100')
    const today = new Date('2020-11-04T18:21:09.731Z')

    it('returns only time for today', () => {
        expect(compactDateTime(today, now)).toEqual('19:21')
    })

    it('returns times before today with weekday', () => {
        const yesterday = new Date('2020-11-03T08:21:09.731Z')
        expect(compactDateTime(yesterday, now)).toEqual('Tue 09:21')
    })

    it('returns month and day for dates older than one week', () => {
        const last_week = new Date('2020-10-27T08:21:09.731Z')
        expect(compactDateTime(last_week, now)).toEqual('Oct 27')
    })

    it('returns ISO date for dates older than one year', () => {
        const last_year = new Date('2019-11-03T18:21:09.731Z')
        expect(compactDateTime(last_year, now)).toEqual('11/3/2019')
    })
})