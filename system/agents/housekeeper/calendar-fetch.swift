import EventKit
import Foundation

let store = EKEventStore()
let sema = DispatchSemaphore(value: 0)

func isoDate(_ date: Date) -> String {
    let c = Calendar.current.dateComponents([.year, .month, .day, .hour, .minute], from: date)
    return String(format: "%04d-%02d-%02dT%02d:%02d", c.year!, c.month!, c.day!, c.hour!, c.minute!)
}

func run() {
    let windowStart = Calendar.current.startOfDay(for: Date(timeIntervalSinceNow: -1 * 86400))
    let windowEnd   = Date(timeIntervalSinceNow: 14 * 86400)
    let predicate   = store.predicateForEvents(withStart: windowStart, end: windowEnd, calendars: nil)
    let events      = store.events(matching: predicate)

    for event in events {
        let uid     = event.eventIdentifier ?? ""
        let title   = (event.title ?? "").replacingOccurrences(of: "|||", with: "--")
        let start   = isoDate(event.startDate)
        let end     = isoDate(event.endDate)
        let allDay  = event.isAllDay ? "true" : "false"
        let calName = event.calendar.title

        var rsvp = "no-attendees"
        if let attendees = event.attendees, !attendees.isEmpty {
            rsvp = "unknown"
            for att in attendees {
                if att.isCurrentUser {
                    switch att.participantStatus {
                    case .accepted:  rsvp = "accepted"
                    case .declined:  rsvp = "declined"
                    case .tentative: rsvp = "tentative"
                    case .pending:   rsvp = "needs action"
                    default:         rsvp = "unknown"
                    }
                    break
                }
            }
        }

        print("\(uid)|||\(title)|||\(start)|||\(end)|||\(allDay)|||\(calName)|||\(rsvp)")
    }
}

store.requestAccess(to: .event) { granted, _ in
    if granted { run() }
    sema.signal()
}
sema.wait()
