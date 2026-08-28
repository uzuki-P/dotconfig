(() => {
	"use strict";

	function customizeActionRow(urlButton) {
		const row = urlButton.closest("tr");
		if (!row || row.dataset.fileActionsCustomized === "true") {
			return;
		}

		const toolbar = urlButton.closest(".btn-toolbar");
		const urlButtonGroup = urlButton.parentElement;
		if (!toolbar || !urlButtonGroup) {
			return;
		}

		const hotlinkMenuItem = row?.querySelector(
			'a[title="Copy hotlink"][data-clipboard-text]'
		);
		const hotlinkMenu = hotlinkMenuItem?.closest(".dropdown-menu")
			?? urlButtonGroup.querySelector(".dropdown-menu");
		const hotlinkToggle = hotlinkMenu?.previousElementSibling;

		if (hotlinkMenuItem?.dataset.clipboardText) {
			const hotlinkUrl = hotlinkMenuItem.dataset.clipboardText;
			const hotlinkButton = document.createElement("button");
			hotlinkButton.type = "button";
			hotlinkButton.className = "copyurl btn btn-outline-light btn-sm";
			hotlinkButton.title = "Copy hotlink";
			hotlinkButton.dataset.clipboardText = hotlinkUrl;
			hotlinkButton.innerHTML = '<i class="bi bi-copy"></i> Hotlink';
			hotlinkButton.addEventListener("click", () => showToast(1000));
			urlButtonGroup.insertBefore(hotlinkButton, urlButton);

			const fileIdLink = row.querySelector('[id^="url-href-"]');
			if (fileIdLink) {
				fileIdLink.href = hotlinkUrl;
				fileIdLink.title = "Open hotlink";
			}
		}
		hotlinkToggle?.remove();
		hotlinkMenu?.remove();

		const downloadUrl = urlButton.dataset.clipboardText;
		const shareButton = urlButtonGroup.querySelector('button[title="Share"]');
		const shareToggle = urlButtonGroup.querySelector('[id^="shareDropdown-"]');
		const shareMenu = shareToggle?.nextElementSibling;
		shareButton?.remove();
		shareToggle?.remove();
		shareMenu?.remove();

		if (downloadUrl) {
			const qrButton = document.createElement("button");
			qrButton.type = "button";
			qrButton.className = "btn btn-outline-light btn-sm";
			qrButton.title = "Show QR code";
			qrButton.innerHTML = '<i class="bi bi-qr-code"></i> Show QR';
			qrButton.addEventListener("click", () => showQrCode(downloadUrl));
			urlButtonGroup.appendChild(qrButton);
		}

		row.dataset.fileActionsCustomized = "true";
	}

	function customizeFileActions(root) {
		root.querySelectorAll('[id^="url-button-"]').forEach(customizeActionRow);
	}

	function start() {
		customizeFileActions(document);
		new MutationObserver(() => customizeFileActions(document)).observe(document.body, {
			childList: true,
			subtree: true,
		});
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", start, { once: true });
	} else {
		start();
	}
})();
