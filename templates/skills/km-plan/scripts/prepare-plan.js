import fs from "node:fs";
import os from "node:os";
import path from "node:path";

try {
  const directory = fs.mkdtempSync(path.join(path.resolve(os.tmpdir()), "km-plan-"));
  const planPath = path.join(directory, "plan.md");
  fs.writeFileSync(planPath, "", "utf8");
  console.log(planPath);
} catch (error) {
  console.error(`prepare-plan: ${error.message}`);
  process.exitCode = 1;
}
