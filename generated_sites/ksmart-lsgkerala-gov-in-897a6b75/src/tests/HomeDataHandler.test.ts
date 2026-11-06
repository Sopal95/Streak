import { expect, test } from "bun:test";
import handler from "../handlers/HomeDataHandler";

test("HomeDataHandler returns status 200 with PageHead data", async () => {
  const data: any = await handler();
  expect(data.status).toBe(200);
  expect(data.PageHead).toBeDefined();
  expect(typeof data.PageHead.title).toBe("string");
});
