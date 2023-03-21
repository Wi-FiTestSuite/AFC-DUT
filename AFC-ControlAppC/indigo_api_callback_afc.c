
/* Copyright (c) 2020 Wi-Fi Alliance                                                */

/* Permission to use, copy, modify, and/or distribute this software for any         */
/* purpose with or without fee is hereby granted, provided that the above           */
/* copyright notice and this permission notice appear in all copies.                */

/* THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL                    */
/* WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED                    */
/* WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL                     */
/* THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR                       */
/* CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING                        */
/* FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF                       */
/* CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT                       */
/* OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS                          */
/* SOFTWARE. */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/stat.h>
#include <arpa/inet.h>

#include "indigo_api.h"
#include "vendor_specific.h"
#include "utils.h"
#include "wpa_ctrl.h"
#include "indigo_api_callback.h"


/* Save TLVs in afcd_configure and Send in afcd_operation */
char server_url[64];
char geo_area[8];
char ca_cert[S_BUFFER_LEN];

void register_apis() {
    register_api(API_GET_CONTROL_APP_VERSION, NULL, get_control_app_handler);
    //register_api(API_AFC_GET_MAC_ADDR, NULL, afc_get_mac_addr_handler);
    register_api(API_AFCD_CONFIGURE, NULL, afcd_configure_handler);
    register_api(API_AFCD_OPERATION, NULL, afcd_operation_handler);
    register_api(API_AFCD_GET_INFO, NULL, afcd_get_info_handler);
}

static int get_control_app_handler(struct packet_wrapper *req, struct packet_wrapper *resp) {
    char buffer[S_BUFFER_LEN];
#ifdef _VERSION_
    snprintf(buffer, sizeof(buffer), "%s", _VERSION_);
#else
    snprintf(buffer, sizeof(buffer), "%s", TLV_VALUE_APP_VERSION);
#endif

    fill_wrapper_message_hdr(resp, API_CMD_RESPONSE, req->hdr.seq);
    fill_wrapper_tlv_byte(resp, TLV_STATUS, TLV_VALUE_STATUS_OK);
    fill_wrapper_tlv_bytes(resp, TLV_MESSAGE, strlen(TLV_VALUE_OK), TLV_VALUE_OK);
    fill_wrapper_tlv_bytes(resp, TLV_CONTROL_APP_VERSION, strlen(buffer), buffer);
    return 0;
}

static int afcd_get_info_handler(struct packet_wrapper *req, struct packet_wrapper *resp) {
    struct tlv_hdr *tlv;
    int freq , channel;
    char response[S_BUFFER_LEN];

    memset(response, 0, sizeof(response));
    /* Get current center channel */
    channel = 39;
    freq = 5950 + 5*channel;

    fill_wrapper_message_hdr(resp, API_CMD_RESPONSE, req->hdr.seq);
    fill_wrapper_tlv_byte(resp, TLV_STATUS, TLV_VALUE_STATUS_OK);
    fill_wrapper_tlv_bytes(resp, TLV_MESSAGE, strlen(TLV_VALUE_OK), TLV_VALUE_OK);
    snprintf(response, sizeof(response), "%d", freq);
    fill_wrapper_tlv_bytes(resp, TLV_AFC_OPER_FREQ, strlen(response), response);
    snprintf(response, sizeof(response), "%d", channel);
    fill_wrapper_tlv_bytes(resp, TLV_AFC_OPER_CHANNEL, strlen(response), response);
    return 0;
}

#define ELLIPSE 0
#define LINEARPOLYGON 1
#define RADIALPOLYGON 2
static int afcd_configure_handler(struct packet_wrapper *req, struct packet_wrapper *resp) {
    int status = TLV_VALUE_STATUS_OK;
    char *message = TLV_VALUE_OK;
    struct tlv_hdr *tlv;
    int i = 0;
    char security[8];
    char bw[8];

    for (i = 0; i < req->tlv_num; i++) {
        struct indigo_tlv *i_tlv;
        char tlv_value[64];
        i_tlv = get_tlv_by_id(req->tlv[i]->id);
        if (i_tlv) {
                memset(tlv_value, 0, sizeof(tlv_value));
                memcpy(tlv_value, req->tlv[i]->value, req->tlv[i]->len);
                indigo_logger(LOG_LEVEL_DEBUG, "TLV: %s - %s", i_tlv->name, tlv_value);
        }
    }

    tlv = find_wrapper_tlv_by_id(req, TLV_AFC_SERVER_URL);
    if (tlv) {
        memset(server_url, 0, sizeof(server_url));
        memcpy(server_url, tlv->value, tlv->len);
    } else {
        indigo_logger(LOG_LEVEL_ERROR, "Missed TLV: TLV_AFC_SERVER_URL");
        status = TLV_VALUE_STATUS_NOT_OK;
        message = TLV_VALUE_NOT_OK;
        goto done;
    }

    tlv = find_wrapper_tlv_by_id(req, TLV_AFC_CA_CERT);
    if (tlv) {        
        memset(ca_cert, 0, sizeof(ca_cert));
        memcpy(ca_cert, tlv->value, tlv->len);
        if (strlen(ca_cert) > 0)
            indigo_logger(LOG_LEVEL_DEBUG, "Configure root certificate");
        else
            indigo_logger(LOG_LEVEL_DEBUG, "Do not configure root certificate !");
    } else {
        indigo_logger(LOG_LEVEL_ERROR, "Missed TLV: TLV_AFC_CA_CERT");
        status = TLV_VALUE_STATUS_NOT_OK;
        message = TLV_VALUE_NOT_OK;
        goto done;
    }

    /* BSS Configurations: SSID, Security, Passphrase */
    tlv = find_wrapper_tlv_by_id(req, TLV_AFC_SECURITY_TYPE);
    if (tlv) {
        memset(security, 0, sizeof(security));
        memcpy(security, tlv->value, tlv->len);
        if (atoi(security) == 0) {
            indigo_logger(LOG_LEVEL_DEBUG, "Configure SAE");
        }
    }
    tlv = find_wrapper_tlv_by_id(req, TLV_AFC_BANDWIDTH);
    if (tlv) {
        memset(bw, 0, sizeof(bw));
        memcpy(bw, tlv->value, tlv->len);
        if (atoi(bw) == 0) {
            indigo_logger(LOG_LEVEL_DEBUG, "Configure DUT to 20MHz bandwidth");
        } else if (atoi(bw) == 1) {
            indigo_logger(LOG_LEVEL_DEBUG, "Configure DUT to 40MHz bandwidth");
        } else if (atoi(bw) == 2) {
            indigo_logger(LOG_LEVEL_DEBUG, "Configure DUT to 80MHz bandwidth");
        } else if (atoi(bw) == 3) {
            indigo_logger(LOG_LEVEL_DEBUG, "Configure DUT to 160MHz bandwidth");
        }
    }

    /* Mandatory Registration Configurations */
    tlv = find_wrapper_tlv_by_id(req, TLV_AFC_LOCATION_GEO_AREA);
    if (tlv) {
        memset(geo_area, 0, sizeof(geo_area));
        memcpy(geo_area, tlv->value, tlv->len);
        if (atoi(geo_area) == ELLIPSE) {
            tlv = find_wrapper_tlv_by_id(req, TLV_AFC_ELLIPSE_CENTER);
            tlv = find_wrapper_tlv_by_id(req, TLV_AFC_ELLIPSE_MAJOR_AXIS);
            tlv = find_wrapper_tlv_by_id(req, TLV_AFC_ELLIPSE_MINOR_AXIS);
            tlv = find_wrapper_tlv_by_id(req, TLV_AFC_ELLIPSE_ORIENTATION);
        } else if (atoi(geo_area) == LINEARPOLYGON) {
            tlv = find_wrapper_tlv_by_id(req, TLV_AFC_LINEARPOLY_BOUNDARY);
        } else if (atoi(geo_area) == RADIALPOLYGON){
            tlv = find_wrapper_tlv_by_id(req, TLV_AFC_RADIALPOLY_CENTER);
            tlv = find_wrapper_tlv_by_id(req, TLV_AFC_RADIALPOLY_BOUNDARY);
        }
    } else {
        //indigo_logger(LOG_LEVEL_DEBUG, "Missed TLV: TLV_AFC_LOCATION_GEO_AREA");
    }

    /* AFCD vendors should have their own freq_range or global op_class + channel CFI */

done:
    fill_wrapper_message_hdr(resp, API_CMD_RESPONSE, req->hdr.seq);
    fill_wrapper_tlv_byte(resp, TLV_STATUS, status);
    fill_wrapper_tlv_bytes(resp, TLV_MESSAGE, strlen(message), message);
    return 0;
}


static int afcd_operation_handler(struct packet_wrapper *req, struct packet_wrapper *resp) {
    struct tlv_hdr *tlv;
    char req_type[8];
    char frame_bw[8];

    tlv = find_wrapper_tlv_by_id(req, TLV_AFC_DEVICE_RESET);
    if (tlv) {
        indigo_logger(LOG_LEVEL_DEBUG, "Device reset");
        /* Vendor specific: add in vendor_specific_afc.c */
    }
    tlv = find_wrapper_tlv_by_id(req, TLV_AFC_SEND_SPECTRUM_REQ);
    if (tlv) {
        memset(req_type, 0, sizeof(req_type));
        memcpy(req_type, tlv->value, tlv->len);
        if (atoi(req_type) == 0) {
            indigo_logger(LOG_LEVEL_DEBUG, "Send Spectrum request with Channel and Frequency based");
        } else if (atoi(req_type) == 1) {
            indigo_logger(LOG_LEVEL_DEBUG, "Send Spectrum request with Channel based");
        } else if (atoi(req_type) == 2) {
            indigo_logger(LOG_LEVEL_DEBUG, "Send Spectrum request with Frequency based");
        }
    }
    tlv = find_wrapper_tlv_by_id(req, TLV_AFC_POWER_CYCLE);
    if (tlv) {
        indigo_logger(LOG_LEVEL_DEBUG, "Trigger power cycle");
        /* Vendor specific: add in vendor_specific_afc.c */
    }
    tlv = find_wrapper_tlv_by_id(req, TLV_AFC_SEND_TEST_FRAME);
    if (tlv) {
        memset(frame_bw, 0, sizeof(frame_bw));
        memcpy(frame_bw, tlv->value, tlv->len);
        if (atoi(frame_bw) == 0) {
            indigo_logger(LOG_LEVEL_DEBUG, "Trigger DUT to send test frames for 20MHz bandwidth");
        } else if (atoi(frame_bw) == 1) {
            indigo_logger(LOG_LEVEL_DEBUG, "Trigger DUT to send test frames for 40MHz bandwidth");
        } else if (atoi(frame_bw) == 2) {
            indigo_logger(LOG_LEVEL_DEBUG, "Trigger DUT to send test frames for 80MHz bandwidth");
        } else if (atoi(frame_bw) == 3) {
            indigo_logger(LOG_LEVEL_DEBUG, "Trigger DUT to send test frames for 160MHz bandwidth");
        }
    }

    fill_wrapper_message_hdr(resp, API_CMD_RESPONSE, req->hdr.seq);
    fill_wrapper_tlv_byte(resp, TLV_STATUS, TLV_VALUE_STATUS_OK);
    fill_wrapper_tlv_bytes(resp, TLV_MESSAGE, strlen(TLV_VALUE_OK), TLV_VALUE_OK);
    return 0;
}
