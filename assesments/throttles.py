from rest_framework.throttling import UserRateThrottle

class AssessmentsBurstThrottle(UserRateThrottle):
    scope = 'assessments_burst'     # e.g., "30/min"

class AssessmentsSustainedThrottle(UserRateThrottle):
    scope = 'assessments_sustained' # e.g., "300/day"
