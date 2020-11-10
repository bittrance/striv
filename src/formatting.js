export function compactDateTime(date, now) {
    if (date == undefined) {
        return undefined
    }
    if (now == undefined) {
        now = new Date()
    }
    const delta = (
        new Date(now.getFullYear(), now.getMonth(), now.getDate()) -
        new Date(date.getFullYear(), date.getMonth(), date.getDate())
    ) / 86400000
    if (delta < 1) {
        return date.toLocaleString(
            'en-GB',
            { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }
        )
    } else if (delta < 7) {
        return date.toLocaleString(
            'en-GB',
            { weekday: 'short', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }
        )
    } else if (delta < 365) {
        return date.toLocaleString(
            'en-GB',
            { month: 'short', day: '2-digit' }
        )
    } else {
        return date.toLocaleDateString()
    }
}
