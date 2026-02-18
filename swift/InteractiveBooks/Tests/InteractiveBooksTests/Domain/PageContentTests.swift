import Testing

@testable import InteractiveBooksCore

@Suite("PageContent")
struct PageContentTests {
    @Test("valid creation succeeds")
    func validCreation() throws {
        let page = try PageContent(pageNumber: 1, text: "Hello")
        #expect(page.pageNumber == 1)
        #expect(page.text == "Hello")
    }

    @Test("pageNumber less than 1 throws")
    func pageNumberLessThanOneThrows() {
        #expect(throws: BookError.self) {
            try PageContent(pageNumber: 0, text: "Hello")
        }
    }

    @Test("negative pageNumber throws")
    func negativePageNumberThrows() {
        #expect(throws: BookError.self) {
            try PageContent(pageNumber: -1, text: "Hello")
        }
    }
}
