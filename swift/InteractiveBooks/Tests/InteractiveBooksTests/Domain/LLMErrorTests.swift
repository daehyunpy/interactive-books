import Testing

@testable import InteractiveBooksCore

@Suite("LLMError")
struct LLMErrorTests {
    @Test("apiKeyMissing carries message")
    func apiKeyMissingCarriesMessage() {
        let error = LLMError.apiKeyMissing("No key")
        guard case let .apiKeyMissing(message) = error else {
            Issue.record("Expected .apiKeyMissing")
            return
        }
        #expect(message == "No key")
    }

    @Test("apiCallFailed carries message")
    func apiCallFailedCarriesMessage() {
        let error = LLMError.apiCallFailed("API error")
        guard case let .apiCallFailed(message) = error else {
            Issue.record("Expected .apiCallFailed")
            return
        }
        #expect(message == "API error")
    }

    @Test("rateLimited carries message")
    func rateLimitedCarriesMessage() {
        let error = LLMError.rateLimited("Too many requests")
        guard case let .rateLimited(message) = error else {
            Issue.record("Expected .rateLimited")
            return
        }
        #expect(message == "Too many requests")
    }

    @Test("timeout carries message")
    func timeoutCarriesMessage() {
        let error = LLMError.timeout("Timed out")
        guard case let .timeout(message) = error else {
            Issue.record("Expected .timeout")
            return
        }
        #expect(message == "Timed out")
    }

    @Test("unsupportedFeature carries message")
    func unsupportedFeatureCarriesMessage() {
        let error = LLMError.unsupportedFeature("Not supported")
        guard case let .unsupportedFeature(message) = error else {
            Issue.record("Expected .unsupportedFeature")
            return
        }
        #expect(message == "Not supported")
    }
}
