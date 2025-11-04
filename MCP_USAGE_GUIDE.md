# MCP Usage Guide - Quick Reference

**Your MCP Servers:** 9 configured and ready  
**Configuration:** `/home/ubuntu/Sandeep/projects/.kiro/settings/mcp.json`

---

## How to Use Your MCP Servers

MCP servers work **automatically** - just ask Kiro naturally and the right tool will be invoked.

---

## 1. 🌐 Web Content & Search

### exa (Advanced Search)
**Trigger phrases:**
- "Search the web for..."
- "Find information about..."
- "Look up recent articles on..."

**Example:**
```
"Search for the latest developments in quantum computing"
"Find technical articles about React Server Components"
```

### fetch (Web Content Extraction)
**Trigger phrases:**
- "Fetch the content from..."
- "Extract text from this URL..."
- "Get the article from..."

**Example:**
```
"Fetch the content from https://example.com/article"
"Extract the main text from this blog post"
```

**Note:** Currently has dependency issues - use built-in fetch as alternative

---

## 2. 🧠 Reasoning & Analysis

### server-sequential-thinking
**Trigger phrases:**
- "Think through this step by step..."
- "Analyze this problem systematically..."
- "Break down this complex issue..."

**Example:**
```
"Think through how to optimize this database query step by step"
"Analyze the trade-offs between microservices and monolithic architecture"
```

---

## 3. 📚 Documentation & Code

### mcp (DocFork)
**Trigger phrases:**
- "Explain this API documentation..."
- "Generate documentation for..."
- "Help me understand this technical doc..."

**Example:**
```
"Explain the Stripe API documentation for payment intents"
"Generate README documentation for my Python project"
```

---

## 4. 🔍 Browser & Debugging

### chrome-devtools-mcp-2
**Trigger phrases:**
- "Debug this web page..."
- "Inspect the network requests..."
- "Analyze the performance of..."

**Example:**
```
"Debug why this JavaScript isn't loading"
"Inspect the API calls made by this website"
```

### mcp-browserbase (Browser Automation)
**Trigger phrases:**
- "Automate browsing to..."
- "Scrape data from..."
- "Take a screenshot of..."

**Example:**
```
"Scrape the pricing table from competitor.com"
"Take a screenshot of how the site looks on mobile"
```

---

## 5. 💾 Memory & Context

### context7-mcp (Upstash)
**Trigger phrases:**
- "Remember that..."
- "Store this information..."
- "What did we discuss about..."

**Example:**
```
"Remember that our deployment is on AWS Lightsail"
"What did we decide about the database schema?"
```

---

## 6. 🎓 Academic Research

### mcpsemanticscholar
**Trigger phrases:**
- "Find research papers on..."
- "Look up academic articles about..."
- "Search for citations of..."

**Example:**
```
"Find recent research papers on transformer models"
"Look up papers by Geoffrey Hinton on deep learning"
```

---

## 7. 📦 Package Security

### npm-sentinel-mcp
**Trigger phrases:**
- "Check security of..."
- "Audit this package..."
- "Are there vulnerabilities in..."

**Example:**
```
"Check the security of the express package"
"Audit my package.json for vulnerabilities"
```

---

## Quick Examples by Use Case

### Research & Learning
```
"Search for the latest AI developments" → exa
"Find papers on reinforcement learning" → mcpsemanticscholar
"Explain the TensorFlow documentation" → mcp (DocFork)
```

### Development & Debugging
```
"Debug this React component" → chrome-devtools-mcp-2
"Check if lodash has vulnerabilities" → npm-sentinel-mcp
"Generate docs for my API" → mcp (DocFork)
```

### Data Collection
```
"Scrape product prices from amazon.com" → mcp-browserbase
"Fetch the content from this blog" → fetch
"Search for market analysis reports" → exa
```

### Complex Problem Solving
```
"Think through this architecture decision" → server-sequential-thinking
"Analyze this algorithm step by step" → server-sequential-thinking
```

---

## Checking MCP Status

### In Kiro UI:
1. Open the **MCP Server view** in the feature panel
2. See which servers are connected (green dot)
3. Check for any error messages

### Via Command Palette:
1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type "MCP"
3. Select "MCP: Show Server Status"

---

## Troubleshooting

### Server Not Responding?

1. **Check connection:**
   - Look at MCP Server view
   - Green dot = connected
   - Red dot = disconnected

2. **Reconnect:**
   - Command Palette → "MCP: Reconnect All Servers"

3. **Check logs:**
   - View → Output → Select "MCP Servers"

### Tool Not Being Used?

1. **Be more explicit:**
   - Instead of: "Tell me about AI"
   - Try: "Search the web for latest AI news"

2. **Check auto-approve:**
   - Some tools need manual approval
   - Look for approval prompts in Kiro

3. **Verify configuration:**
   - Check `.kiro/settings/mcp.json`
   - Ensure `disabled: false`

---

## Configuration Reference

### Your Current Setup

```json
{
  "mcpServers": {
    "fetch": { "disabled": false, "autoApprove": ["fetch"] },
    "exa": { "disabled": false },
    "server-sequential-thinking": { "disabled": false },
    "mcp": { "disabled": false },
    "chrome-devtools-mcp-2": { "disabled": false },
    "context7-mcp": { "disabled": false },
    "mcp-browserbase": { "disabled": false },
    "mcpsemanticscholar": { "disabled": false },
    "npm-sentinel-mcp": { "disabled": false }
  }
}
```

### To Enable Auto-Approve for a Tool:

```json
"tool-name": {
  "disabled": false,
  "autoApprove": ["tool_function_name"]
}
```

### To Disable a Server:

```json
"tool-name": {
  "disabled": true
}
```

---

## Best Practices

1. **Be Specific:** Clear requests get better tool selection
2. **Check Approvals:** Review what tools are doing before approving
3. **Monitor Usage:** Watch the MCP Server view to learn patterns
4. **Restart When Needed:** After config changes, restart Kiro
5. **Keep Updated:** MCP servers update automatically via Smithery

---

## Support & Resources

- **Smithery Dashboard:** https://smithery.ai
- **MCP Documentation:** https://modelcontextprotocol.io
- **Kiro MCP Guide:** Command Palette → "Help: MCP Documentation"

---

## Summary

✅ **9 MCP servers configured**  
✅ **All enabled and ready**  
✅ **Smithery API key configured**  
✅ **Auto-approve set for fetch**

Just use Kiro naturally - the right tools will activate automatically!
