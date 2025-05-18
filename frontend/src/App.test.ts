import { mount, unmount } from 'svelte';
import { describe, test, expect, vi } from 'vitest';
import { render } from '@testing-library/svelte';
import App from './App.svelte';

import * as sample_response from '../sample_response.json';


test('App', async () => {
    //render(App);
    const component = mount(App, {
        target: document.body
    });
    unmount(component);
});

test('load event', () => {
    const component = mount(App, {
        target: document.body
    });

    window.dispatchEvent(new Event('load'));
    unmount(component);
});

test('Change Width', async () => {
    const component = mount(App, {
        target: document.body
    });
    // Default width
    expect(document.getElementById("feed_grid").style).toContain('grid-template-columns: 1fr 1fr 1fr')

    // Tablet mode
    window.innerWidth = 800;
    window.dispatchEvent(new Event('resize'));
    expect(document.getElementById("feed_grid").style).toContain('grid-template-columns: 1fr 1fr')

    // Mobile mode
    window.innerWidth = 500;
    window.dispatchEvent(new Event('resize'));
    expect(document.getElementById("feed_grid").style).toContain('grid-template-columns: 1fr')

    // Desktop mode
    window.innerWidth = 1200;
    window.dispatchEvent(new Event('resize'));
    expect(document.getElementById("feed_grid").style).toContain('grid-template-columns: 1fr 1fr 1fr')

    unmount(component);
});

test("generateURL", () => {
    const component = mount(App, {
        target: document.body
    });
    
    window.dispatchEvent(new Event('load'));
    let query = "testQuery";
    let key = "testKey";
    let page = "1";
    expect(component.generateURL(query, page, key)).toBe(`https://api.nytimes.com/svc/search/v2/articlesearch.json?q=${query}&api-key=${key}&page=${page}`)

    unmount(component);
})

test("fetchKey", async() => {
    let originalFetch = window.fetch;

    const component = mount(App, {
        target: document.body
    });
    
    const mockResponse = {
        apiKey: "testKey"
    };
    window.fetch = vi.fn(() =>
        Promise.resolve({
            json: () => Promise.resolve(mockResponse),
        }),
    );
    const data = await component.fetchKey();
    expect(data).toEqual(mockResponse.apiKey);
    
    window.fetch = originalFetch;
    
    unmount(component);
})

test("fetchData", async() => {
    let originalFetch = window.fetch;

    const component = mount(App, {
        target: document.body
    });
    
    const mockResponse = {
        apiKey: "testKey"
    };
    window.fetch = vi.fn(() =>
        Promise.resolve({
            json: () => Promise.resolve(mockResponse),
        }),
    );
    const data = await component.fetchData(1);
    expect(data).toEqual(mockResponse.apiKey);
    
    window.fetch = originalFetch;
    
    unmount(component);
})

test('displayDate', () => {
    const component = mount(App, {
        target: document.body
    });
    window.dispatchEvent(new Event('load'));

    let dateArr = document.getElementById("header_date_date").innerHTML.split(" ");
    console.log(dateArr);

    const possibleWeekdays = ["Sunday,", "Monday,", "Tuesday,", "Wednesday,", "Thursday,", "Friday,", "Saturday,"];
    const possibleMonths = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const possibleDays = ["1,", "2,", "3,", "4,", "5,", "6,", "7,", "8,", "9,", "10,", "11,", "12,", "13,", "14,", "15,", "16,", "17,", "18,", "19,", "20,", "21,", "22,", "23,", "24,", "25,", "26,", "27,", "28,", "29,", "30,", "31,"];
    const possibleYears = ["2025", "2026", "2027", "2028", "2029", "2030"];
    expect(possibleWeekdays).toContain(dateArr[0]);
    expect(possibleMonths).toContain(dateArr[1]);
    expect(possibleDays).toContain(dateArr[2]);
    expect(possibleYears).toContain(dateArr[3]);

    unmount(component);
});
