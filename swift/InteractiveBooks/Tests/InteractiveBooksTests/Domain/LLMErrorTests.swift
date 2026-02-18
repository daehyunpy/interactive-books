@testable import InteractiveBooksCore
import Testing

@Suite("LLMError")
struct LLMErrorTests {
    @Test("each case preserves its message")
    func eachCasePreservesMessage() {
        #expect(LLMError.apiKeyMissing("a") != LLMError.apiKeyMissing("b"))
        #expect(LLMError.apiCallFailed("a") != LLMError.apiCallFailed("b"))
        #expect(LLMError.rateLimited("a") != LLMError.rateLimited("b"))
        #expect(LLMError.timeout("a") != LLMError.timeout("b"))
        #expect(LLMError.unsupportedFeature("a") != LLMError.unsupportedFeature("b"))
    }

    @Test("different cases are not equal")
    func differentCasesAreNotEqual() {
        #expect(LLMError.apiKeyMissing("x") != LLMError.timeout("x"))
    }
}
