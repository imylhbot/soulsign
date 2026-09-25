import BackgroundTasks
import Foundation

/// Best-effort automatic renewal coordinator.
///
/// iOS does not guarantee an exact execution time for BGAppRefreshTask. The app also
/// performs the same 24-hour expiry check when it becomes active and uses the upstream
/// local-notification expiry scheduler as a fallback.
@MainActor
final class SoulSignBackgroundRenewal {
    static let taskIdentifier = "com.soulsign.app.autorenew"

    private unowned let appsViewModel: AppsViewModel
    private var registered = false

    init(appsViewModel: AppsViewModel) {
        self.appsViewModel = appsViewModel
    }

    func register() {
        guard registered == false else { return }
        registered = BGTaskScheduler.shared.register(
            forTaskWithIdentifier: Self.taskIdentifier,
            using: nil
        ) { [weak self] task in
            guard let task = task as? BGAppRefreshTask else {
                task.setTaskCompleted(success: false)
                return
            }

            let worker = Task { @MainActor [weak self] in
                guard let self else {
                    task.setTaskCompleted(success: false)
                    return
                }
                let succeeded = await self.appsViewModel.soulSignAutoRenewInBackground()
                task.setTaskCompleted(success: succeeded)
                self.schedule()
            }
            task.expirationHandler = {
                worker.cancel()
            }
        }
    }

    func schedule() {
        BGTaskScheduler.shared.cancel(taskRequestWithIdentifier: Self.taskIdentifier)
        let request = BGAppRefreshTaskRequest(identifier: Self.taskIdentifier)
        // Ask for another opportunity in ~6h. This is only the earliest allowed time;
        // iOS may launch substantially later based on battery/network/usage heuristics.
        request.earliestBeginDate = Date(timeIntervalSinceNow: 6 * 60 * 60)
        do {
            try BGTaskScheduler.shared.submit(request)
        } catch {
            // Foreground expiry checking + notifications remain as the fallback.
        }
    }
}
