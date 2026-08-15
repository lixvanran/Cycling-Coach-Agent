// 截图脚本 - 用 puppeteer-core 切页后截图
import puppeteer from "puppeteer-core";
import { writeFileSync } from "fs";

const CHROME = "/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome";
const BASE = "http://127.0.0.1:1420";
const OUT = "/workspace/cycling-coach/assets/screenshots";

async function main() {
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
    headless: true,
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  // 1) Dashboard (默认)
  await page.goto(BASE, { waitUntil: "networkidle0", timeout: 15000 });
  await new Promise((r) => setTimeout(r, 1000));
  await page.screenshot({ path: `${OUT}/01-dashboard.png`, fullPage: true });
  console.log("✓ 01-dashboard.png");

  // 2) Activities (用 zustand 直接切)
  await page.evaluate(() => {
    // 从 useAppStore 拿 setView
    // zustand 在 window 上没暴露,但我们可以用 click 触发
    // 找 "训练" 链接
    const links = Array.from(document.querySelectorAll("div.nav-link, [class*='nav-link']"));
    const target = links.find((el) => el.textContent.includes("训练"));
    if (target) target.click();
  });
  await new Promise((r) => setTimeout(r, 1500));
  await page.screenshot({ path: `${OUT}/02-activities.png`, fullPage: true });
  console.log("✓ 02-activities.png");

  // 3) Activity Detail (点第一行)
  await page.evaluate(() => {
    const rows = document.querySelectorAll("table tbody tr");
    if (rows[0]) rows[0].click();
  });
  await new Promise((r) => setTimeout(r, 2500));
  await page.screenshot({ path: `${OUT}/03-activity-detail.png`, fullPage: true });
  console.log("✓ 03-activity-detail.png");

  // 4) Import
  await page.evaluate(() => {
    const links = Array.from(document.querySelectorAll("div.nav-link, [class*='nav-link']"));
    const target = links.find((el) => el.textContent.includes("导入"));
    if (target) target.click();
  });
  await new Promise((r) => setTimeout(r, 1500));
  await page.screenshot({ path: `${OUT}/04-import.png`, fullPage: true });
  console.log("✓ 04-import.png");

  // 5) Profile
  await page.evaluate(() => {
    const links = Array.from(document.querySelectorAll("div.nav-link, [class*='nav-link']"));
    const target = links.find((el) => el.textContent.includes("个人画像"));
    if (target) target.click();
  });
  await new Promise((r) => setTimeout(r, 1500));
  await page.screenshot({ path: `${OUT}/05-profile.png`, fullPage: true });
  console.log("✓ 05-profile.png");

  await browser.close();
  console.log("All done.");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
