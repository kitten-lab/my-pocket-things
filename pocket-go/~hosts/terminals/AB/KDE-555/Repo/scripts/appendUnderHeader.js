module.exports = async (params) => {
    const header = params.variables.header;
    const newThoughts = params.variables.newThoughts;
    const highlight = params.variables.highlight;
    const logFile = params.variables.logFile;

    const file = await app.vault.getAbstractFileByPath(params.filePath);
    let content = await app.vault.read(file);

    // Build the block to insert
    const block = `> ${highlight}\n\n##### New thoughts:\n${newThoughts}\n\nlogged from → [[${logFile}]]\n<sup>capture CHRONOKEY:: | ${moment().format("MM/DD/YYYY-YYYY[Q]Q:WW-MM:ddd-DD[A].X[N]")}</sup>\n`;

    // Look for existing header
    const headerRegex = new RegExp(`^## ${header}$`, "m");

    if (headerRegex.test(content)) {
        // Header exists: insert below it
        content = content.replace(headerRegex, `## ${header}\n${block}`);
    } else {
        // Header doesn’t exist: create new header at bottom
        content += `\n## ${header}\n${block}`;
    }

    await app.vault.modify(file, content);
};
