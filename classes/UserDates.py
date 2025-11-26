class UserDates:
    def __init__(self, data):
        self.last_connection_at = data["lastConnectionAt"]
        self.last_notification_check_at = data["lastNotificationsCheckAt"]
        self.last_country_message_check_at = data["lastCountryMessageCheckAt"]
        self.last_global_message_check_at = data["lastGlobalMessageCheckAt"]
        self.last_events_check_at = data["lastEventsCheckAt"]
        self.last_work_offer_applications = data["lastWorkOfferApplications"]
        self.last_work_at = data.get("lastWorkAt", None)
        self.last_skills_reset_at = data.get("lastSkillsResetAt", "0001-01-01T00:00:00Z")