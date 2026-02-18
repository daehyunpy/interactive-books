import Testing

@testable import InteractiveBooksCore

@Test func coreLibraryVersion() {
    #expect(InteractiveBooksCore.version == "0.1.0")
}
