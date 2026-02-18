# Chapter 1: Introduction

This is a sample Markdown book used for testing the ingestion pipeline. It contains headings, paragraphs, and formatting to verify that the Markdown parser correctly extracts text and splits by heading boundaries.

## Background

The interactive books project supports multiple file formats. Markdown files are split into logical pages at **H1** and **H2** heading boundaries.

# Chapter 2: Details

This chapter covers additional details about the project. Each heading-based section becomes a separate logical page.

Inline formatting like *italics*, **bold**, `code`, and [links](http://example.com) should be stripped to plain text during parsing.

## Summary

The downstream chunker handles splitting large sections into appropriately sized pieces for embedding and retrieval.
