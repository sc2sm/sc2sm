PR Summary Instructions:
Generate a comprehensive summary of each pull request optimized for social media content creation. Provide extensive detail in the following bullet point format:

- PR Link: Provide a hyperlink to the pull request from the 'URL:' value
- Title: Provide the value of the 'Title:' field
- PR State: Provide the state of the PR based on the following conditions:
  - If 'Merged: true' set 'PR State: 🔀 Merged'
  - Else If 'Draft: true' set 'PR State: 📝 Draft'
  - Else If 'State: open' or 'State: active' set 'PR State: 💬 Open'
  - Else If 'State: closed' or 'State: DECLINED' and 'Merged: false' set 'PR State: 🔒 Closed'
  - Else set 'PR State: ❓ Unknown'
  - If the PR is stale, add '⚠️ Stale' at the end of the PR State.
- Mergeable (if PR State is not 'Merged'): Provide the mergeable status of the PR as 'Mergeable' or 'Not Mergeable' based on the "Mergeable: " value.
- PR Stage (if PR State is not 'Merged'): Provide the stage of the PR based on the "PR Stage: " value.
- Extensive Summary: Provide a comprehensive 200-300 word analysis covering:
  • Core functionality and features added/changed
  • Technical architecture and implementation approach
  • Dependencies, frameworks, or tools introduced
  • Performance implications and optimizations
  • Security considerations and improvements
  • User experience changes and benefits
  • Integration points with existing systems
  • Potential risks, edge cases, or technical debt
  • Business value and impact on product goals
  • Developer experience improvements
  • Testing strategy and coverage added
  • Documentation changes or requirements
- Technical Details: Break down specific technical aspects:
  • Programming languages and frameworks used
  • Database schema changes or migrations
  • API endpoints added/modified
  • Configuration changes required
  • Infrastructure or deployment considerations
  • Third-party integrations or services
  • Code patterns or architectural decisions
- Social Media Angles: Identify compelling narratives for social posts:
  • Achievement/milestone reached (new feature launch, performance gain, etc.)
  • Problem solved (bug fix, user pain point addressed, etc.)
  • Learning/insight gained (technical discovery, best practice adopted, etc.)
  • Innovation/experimentation (new technology tried, creative solution, etc.)
  • Collaboration/teamwork (code review insights, pair programming, etc.)
  • Progress update (iteration on existing feature, incremental improvement, etc.)
- Hook Ideas: Suggest attention-grabbing opening lines for social posts:
  • "Just shipped..." for completed features
  • "Finally fixed..." for bug resolutions
  • "Discovered that..." for technical insights
  • "Experimenting with..." for new approaches
  • "Optimized..." for performance improvements
  • "Simplified..." for refactoring or UX improvements
- Comments: Provide an extensive review of what changed and the larger context. Include detailed analysis of all comments found within <pr_comments>, mentioning each comment author's username from <comment_author_username>. Cover the technical changes, architectural decisions, potential impacts, and any concerns raised. If there are no comments available, output 'No comments'.
- Next Steps: Provide clear, actionable guidance for what the dev team needs to do next. If the PR is merged, tell the author what follow-up action they should take. If the PR is not yet merged, tailor the guidance based on the "PR Stage:" value. If waiting on reviewers, instruct reviewers what they need to test, review and validate before approving. Otherwise instruct the author on the actions needed to move the PR forward, if they need to address any issues or respond to any feedback.

Example Output Format:

- **PR Link:** [#3001](https://github.com/mygithuborg/myrepo/pull/3001)
- **Title:** Add user authentication system
- **PR State:** 🔀 Merged
- **Extensive Summary:** This PR introduces a comprehensive user authentication system using JWT tokens and bcrypt password hashing. The implementation includes login/logout functionality, user registration with email verification, password reset capabilities, and role-based access control. The authentication middleware integrates seamlessly with existing API endpoints, providing session management and automatic token refresh. Security measures include rate limiting on login attempts, password strength validation, and secure cookie handling. The system uses PostgreSQL for user data storage with proper indexing for performance. This addition significantly enhances the application's security posture while maintaining a smooth user experience. The modular design allows for easy extension with OAuth providers in the future. Comprehensive test coverage ensures reliability and edge case handling.
- **Technical Details:** Built with Node.js and Express framework, uses JSON Web Tokens (JWT) for stateless authentication, bcrypt for password hashing with salt rounds, PostgreSQL database with user and session tables, Redis for session storage and rate limiting, middleware pattern for route protection, environment-based configuration management, input validation using Joi schemas, and automated email service integration using SendGrid.
- **Social Media Angles:** Major milestone - Authentication system launch, Security improvement - Enhanced user data protection, Developer experience - Streamlined login flow, Technical achievement - JWT implementation from scratch, User experience - Seamless registration process.
- **Hook Ideas:** "Just shipped secure user auth...", "Finally solved the login puzzle...", "Built our authentication from the ground up...", "Securing user data with...", "Authentication system is live..."
- **Comments:** No comments.
- **Next Steps:** Deploy to staging environment, configure SendGrid API keys, update frontend to integrate with new auth endpoints, run security audit, and prepare user migration plan for existing accounts.
