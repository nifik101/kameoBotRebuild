# API Documentation Review & Validation Prompt

## Purpose
This prompt provides comprehensive instructions for reviewing, validating, comparing, and updating multiple API documentation files to ensure consistency, accuracy, and proper structure.

## Review Instructions

### 1. **Document Inventory & Structure Analysis**

#### A. Identify All Documentation Files
```bash
# List all documentation files in the project
find . -name "*.md" -path "*/docs/*" | grep -i api
```

#### B. Categorize Documents by Purpose
- **Index/Overview**: Navigation and high-level summaries
- **Technical Reference**: Complete API specifications
- **User Guides**: Business-focused documentation
- **Quick Start**: Getting started guides
- **Examples**: Implementation examples and code samples
- **Architecture**: System design and structure

#### C. Validate Document Hierarchy
- Ensure logical flow from overview → technical details → examples
- Check that index files properly reference all other documents
- Verify no circular references or broken links

### 2. **Content Validation & Cross-Reference Check**

#### A. API Endpoint Consistency
For each documented endpoint, verify:
- **URL Path**: Consistent across all documents
- **HTTP Method**: Same method in all references
- **Parameters**: Identical parameter names and types
- **Response Structure**: Consistent JSON structure
- **Headers**: Same required headers everywhere
- **Rate Limiting**: Consistent limits and handling

#### B. Code Example Validation
- **Syntax**: All code examples are syntactically correct
- **Consistency**: Same variable names and patterns across documents
- **Completeness**: Examples include all required imports and setup
- **Accuracy**: Code matches actual API behavior

#### C. Configuration Consistency
- **Environment Variables**: Same variable names and descriptions
- **Default Values**: Consistent defaults across documents
- **Required vs Optional**: Clear distinction maintained

### 3. **Redundancy & Duplication Analysis**

#### A. Content Duplication Check
Identify and resolve:
- **Exact Duplicates**: Identical content in multiple files
- **Near Duplicates**: Similar content with minor variations
- **Fragmented Information**: Related information split across files
- **Outdated Versions**: Old information that conflicts with current

#### B. Information Architecture Review
- **Single Source of Truth**: Each piece of information has one authoritative location
- **Cross-References**: Use links instead of duplicating content
- **Progressive Disclosure**: Start simple, add complexity in layers

### 4. **Accuracy & Completeness Validation**

#### A. API Coverage Verification
- **All Endpoints**: Every discovered API endpoint is documented
- **All Parameters**: Complete parameter lists with descriptions
- **All Response Fields**: Full response structure documentation
- **Error Handling**: All error scenarios and codes documented
- **Authentication**: Complete auth flow documentation

#### B. Real Data Validation
- **HAR File Correlation**: All documentation matches actual network captures
- **Production Testing**: Verify against real API responses
- **Version Consistency**: API version numbers match across documents

### 5. **Structure & Organization Review**

#### A. Document Structure Standards
- **Consistent Headers**: Same header hierarchy across documents
- **Table of Contents**: Proper navigation structure
- **Code Block Formatting**: Consistent syntax highlighting
- **Link Structure**: Proper internal and external linking

#### B. Information Flow
- **Logical Progression**: Information builds from basic to advanced
- **Dependency Order**: Prerequisites are documented before dependent features
- **Cross-References**: Proper linking between related concepts

### 6. **Quality Assurance Checklist**

#### A. Technical Accuracy
- [ ] All API endpoints match actual implementation
- [ ] Request/response examples are valid JSON
- [ ] HTTP status codes are correct
- [ ] Authentication flows are complete
- [ ] Error handling is comprehensive

#### B. Content Quality
- [ ] No spelling or grammar errors
- [ ] Consistent terminology throughout
- [ ] Clear and concise explanations
- [ ] Appropriate level of detail for target audience
- [ ] Code examples are complete and runnable

#### C. Structure Quality
- [ ] Logical document organization
- [ ] Proper cross-referencing
- [ ] No broken links
- [ ] Consistent formatting
- [ ] Appropriate use of tables, lists, and code blocks

### 7. **Specific Review Tasks**

#### A. Index File Validation
```markdown
# Check index file (kameo_api_index.md)
- [ ] Lists all other documentation files
- [ ] Provides clear navigation structure
- [ ] Describes purpose of each document
- [ ] Includes quick start guide
- [ ] References implementation examples
```

#### B. Technical Reference Validation
```markdown
# Check technical reference (kameo_api_technical_reference.md)
- [ ] Complete endpoint documentation
- [ ] All cURL examples work
- [ ] Response structures are accurate
- [ ] Error handling is documented
- [ ] Rate limiting information is correct
```

#### C. User Guide Validation
```markdown
# Check user guide (kameo_api_user_guide.md)
- [ ] Business-focused language
- [ ] Clear use cases and workflows
- [ ] Non-technical explanations
- [ ] Practical examples
- [ ] Links to technical details when needed
```

#### D. Quick Start Validation
```markdown
# Check quick start (kameo_api_quickstart.md)
- [ ] Step-by-step instructions
- [ ] Complete working examples
- [ ] All required setup steps
- [ ] Troubleshooting section
- [ ] Links to detailed documentation
```

#### E. Examples Validation
```markdown
# Check examples (kameo_api_examples.md)
- [ ] All code examples are complete
- [ ] Examples demonstrate real use cases
- [ ] Error handling is included
- [ ] Best practices are shown
- [ ] Code is production-ready
```

### 8. **Update & Maintenance Instructions**

#### A. Content Updates
1. **Identify Changes**: What has changed in the API or system?
2. **Impact Analysis**: Which documents are affected?
3. **Update Strategy**: How to propagate changes across documents?
4. **Validation**: How to verify updates are correct?

#### B. Version Control
- **Change Tracking**: Document what was changed and why
- **Review Process**: Who reviews documentation changes?
- **Publication Process**: How are updates published?

#### C. Maintenance Schedule
- **Regular Reviews**: How often to review documentation?
- **Update Triggers**: What events trigger documentation updates?
- **Quality Metrics**: How to measure documentation quality?

### 9. **Common Issues & Resolution**

#### A. Inconsistency Issues
- **Problem**: Same information differs across documents
- **Solution**: Establish single source of truth, use cross-references
- **Prevention**: Regular consistency checks

#### B. Outdated Information
- **Problem**: Documentation doesn't match current API
- **Solution**: Update based on latest HAR files or API changes
- **Prevention**: Automated validation against real API

#### C. Redundancy Issues
- **Problem**: Same information repeated in multiple places
- **Solution**: Consolidate into single location, use references
- **Prevention**: Content planning and review process

#### D. Structure Issues
- **Problem**: Poor organization or navigation
- **Solution**: Restructure based on user needs and logical flow
- **Prevention**: Information architecture planning

### 10. **Validation Commands & Tools**

#### A. Automated Checks
```bash
# Check for broken links
find . -name "*.md" -exec grep -l "\[.*\](" {} \; | xargs -I {} markdown-link-check {}

# Check for duplicate content
find . -name "*.md" -exec shasum {} \; | sort | uniq -d

# Validate JSON examples
find . -name "*.md" -exec grep -A 20 "```json" {} \; | jq .
```

#### B. Manual Review Checklist
- [ ] Read each document from start to finish
- [ ] Follow all links and verify they work
- [ ] Test all code examples
- [ ] Verify all API calls against real endpoints
- [ ] Check for consistency in terminology
- [ ] Validate all configuration examples

### 11. **Final Review Questions**

#### A. Completeness
- Does the documentation cover everything a developer needs to know?
- Are there any gaps in the information provided?
- Is the level of detail appropriate for the target audience?

#### B. Accuracy
- Does the documentation match the actual API behavior?
- Are all examples tested and working?
- Is the information up-to-date with the latest changes?

#### C. Usability
- Is the documentation easy to navigate and understand?
- Can users find what they need quickly?
- Are there clear paths from basic to advanced information?

#### D. Maintenance
- Is the documentation structure sustainable for future updates?
- Are there clear processes for keeping it current?
- Is the quality high enough to justify the maintenance effort?

## Usage Instructions

1. **Run this review process** whenever:
   - New API endpoints are discovered
   - Existing endpoints change
   - Documentation structure is modified
   - Major system updates occur

2. **Use the checklist systematically** to ensure no aspect is missed

3. **Document all findings** and create action items for improvements

4. **Schedule regular reviews** to maintain documentation quality

5. **Involve stakeholders** in the review process for different perspectives

This prompt ensures comprehensive, accurate, and well-structured API documentation that serves users effectively and can be maintained efficiently over time. 