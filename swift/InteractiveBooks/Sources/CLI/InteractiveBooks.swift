import ArgumentParser
import InteractiveBooksCore

@main
struct InteractiveBooksCLI: ParsableCommand {
    static let configuration = CommandConfiguration(
        commandName: "interactive-books",
        abstract: "Interactive Books — chat with your books using AI",
        version: InteractiveBooksCore.version,
        subcommands: [BooksCommand.self],
    )
}
