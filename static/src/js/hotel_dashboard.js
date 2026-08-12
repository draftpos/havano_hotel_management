/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

export class HotelDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        
        this.state = useState({
            filterStatus: 'all',
            searchStatus: 'all',
            searchRoomType: 'all',
            searchFloor: 'all',
            searchRoomName: '',
            stats: {
                vacant: 0, occupied: 0, reserved: 0,
                dirty: 0, out_of_order: 0, all_rooms: 0
            },
            rooms: [],
            roomTypes: [],
            floors: [],
            hasActiveShift: false,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    setFilter(status) {
        this.state.filterStatus = status;
    }

    clearFilters() {
        this.state.filterStatus = 'all';
        this.state.searchStatus = 'all';
        this.state.searchRoomType = 'all';
        this.state.searchFloor = 'all';
        this.state.searchRoomName = '';
    }

    get filteredRooms() {
        let result = this.state.rooms;

        // Apply Card Filter
        if (this.state.filterStatus && this.state.filterStatus !== 'all') {
            if (this.state.filterStatus === 'dirty' || this.state.filterStatus === 'out_of_order') {
                result = result.filter(r => r.housekeeping_status === this.state.filterStatus);
            } else {
                result = result.filter(r => r.status === this.state.filterStatus);
            }
        }

        // Apply Dropdown Filters
        if (this.state.searchStatus !== 'all') {
            result = result.filter(r => r.status === this.state.searchStatus);
        }
        if (this.state.searchRoomType !== 'all') {
            result = result.filter(r => r.room_type_id && r.room_type_id[0] === parseInt(this.state.searchRoomType));
        }
        if (this.state.searchFloor !== 'all') {
            result = result.filter(r => r.floor_id && r.floor_id[0] === parseInt(this.state.searchFloor));
        }
        if (this.state.searchRoomName.trim() !== '') {
            const query = this.state.searchRoomName.toLowerCase();
            result = result.filter(r => r.name.toLowerCase().includes(query) || (r.guest_name && r.guest_name.toLowerCase().includes(query)));
        }

        return result;
    }

    async loadData() {
        const data = await this.orm.call("hotel.room", "get_dashboard_data", []);
        if (data) {
            this.state.stats = data.stats;
            this.state.rooms = data.rooms;
            this.state.roomTypes = data.room_types;
            this.state.floors = data.floors;
            this.state.hasActiveShift = data.has_active_shift;
        }
    }
    
    async refreshDashboard() {
        await this.loadData();
    }

    addRoom() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Add Room",
            res_model: "hotel.room",
            views: [[false, "form"]],
            target: "new",
        }, {
            onClose: () => {
                this.refreshDashboard();
            }
        });
    }

    async openShift() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Hotel Shift",
            res_model: "hotel.shift.wizard",
            views: [[false, "form"]],
            target: "new",
        });
    }

    async openPOS() {
        // Placeholder for Restaurant POS logic
    }

    async openCheckIn() {
        const selectedRooms = this.state.rooms.filter(r => r.selected);
        if (selectedRooms.length > 1) {
            alert("Please select only one room at a time!");
            return;
        }
        const selectedRoom = selectedRooms[0];
        
        if (selectedRoom && selectedRoom.status === 'occupied') {
            alert(`Room ${selectedRoom.name} is currently occupied!`);
            return;
        }
        
        const context = selectedRoom ? { default_room_id: selectedRoom.id } : {};

        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Check In",
            res_model: "hotel.checkin",
            views: [[false, "form"]],
            target: "new",
            context: context,
        }, {
            onClose: () => {
                this.refreshDashboard();
            }
        });
    }

    async openCheckOut() {
        const selectedRooms = this.state.rooms.filter(r => r.selected);
        if (selectedRooms.length > 1) {
            alert("Please select only one room at a time!");
            return;
        }
        const selectedRoom = selectedRooms[0];
        const context = selectedRoom ? { default_room_id: selectedRoom.id } : {};
        
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Check Out",
            res_model: "hotel.checkout",
            views: [[false, "form"]],
            target: "new",
            context: context,
        }, {
            onClose: () => {
                this.refreshDashboard();
            }
        });
    }

    async openReservation() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Reservation",
            res_model: "hotel.reservation",
            views: [[false, "form"]],
            target: "new",
        }, {
            onClose: () => {
                this.refreshDashboard();
            }
        });
    }

    async openPayment() {
        const selectedRooms = this.state.rooms.filter(r => r.selected);
        if (selectedRooms.length > 1) {
            alert("Please select only one room at a time!");
            return;
        }
        const selectedRoom = selectedRooms[0];
        const context = selectedRoom ? { default_room_id: selectedRoom.id } : {};
        
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Make Payment",
            res_model: "hotel.payment.wizard",
            views: [[false, "form"]],
            target: "new",
            context: context,
        }, {
            onClose: () => {
                this.refreshDashboard();
            }
        });
    }

    async openExtraCharge() {
        const selectedRooms = this.state.rooms.filter(r => r.selected);
        if (selectedRooms.length > 1) {
            alert("Please select only one room at a time!");
            return;
        }
        const selectedRoom = selectedRooms[0];
        let context = {
            default_move_type: 'out_invoice',
        };
        
        if (selectedRoom) {
            if (selectedRoom.current_guest_id && selectedRoom.current_guest_id[0]) {
                context.default_partner_id = selectedRoom.current_guest_id[0];
            }
            if (selectedRoom.current_checkin_id && selectedRoom.current_checkin_id[0]) {
                context.default_hotel_checkin_id = selectedRoom.current_checkin_id[0];
            }
        }
        
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Extra Charge",
            res_model: "account.move",
            views: [[false, "form"]],
            target: "new",
            context: context,
        });
    }

    async openMoveRoom() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Move Room (Select Check-In)",
            res_model: "hotel.checkin",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    async openExtendStay() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Extend Stay (Select Check-In)",
            res_model: "hotel.checkin",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    async openHousekeepingWizard(roomId, currentStatus) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Update House Keeping Status",
            res_model: "hotel.housekeeping.wizard",
            views: [[false, "form"]],
            target: "new",
            context: {
                default_room_id: roomId,
                default_housekeeping_status: currentStatus,
            },
        }, {
            onClose: () => {
                this.refreshDashboard();
            }
        });
    }

    async printReceipt(roomId) {
        const action = await this.orm.call("hotel.room", "action_print_receipt", [[roomId]]);
        if (action) {
            this.action.doAction(action);
        }
    }

    async openPOS() {
        this.action.doAction("point_of_sale.action_pos_config_kanban");
    }
}

HotelDashboard.template = "havano_hotel_management.HotelDashboard";

registry.category("actions").add("havano_hotel_management.hotel_dashboard", HotelDashboard);
