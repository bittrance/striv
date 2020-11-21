export function compactDateTime(date, testNow) {
    let now, timeZone
    if (date == undefined) {
        return undefined
    }
    if (testNow == undefined) {
        now = new Date()
        timeZone = undefined
    } else {
        [now, timeZone] = testNow
    }
    const delta = (
        new Date(now.getFullYear(), now.getMonth(), now.getDate()) -
        new Date(date.getFullYear(), date.getMonth(), date.getDate())
    ) / 86400000
    if (delta < 1) {
        return 'Today ' + date.toLocaleString(
            'en-GB',
            { hour: '2-digit', minute: '2-digit', hourCycle: 'h23', timeZone }
        )
    } else if (delta < 7) {
        return date.toLocaleString(
            'en-GB',
            { weekday: 'short', hour: '2-digit', minute: '2-digit', hourCycle: 'h23', timeZone }
        )
    } else if (delta < 365) {
        return date.toLocaleString(
            'en-GB',
            { month: 'short', day: '2-digit', timeZone }
        )
    } else {
        return date.toLocaleDateString('en-GB', { timeZone })
    }
}

export function statusClass(status) {
    if (status == "pending") {
        return "fas fa-hourglass-half text-secondary";
    } else if (status == "running") {
        return "fas fa-play text-warning";
    } else if (status == "successful") {
        return "fas fa-check text-success";
    } else if (status == "failed") {
        return "fas fa-times-circle text-danger";
    }
}