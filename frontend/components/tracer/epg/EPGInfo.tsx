import * as React from 'react';
import Box from '@mui/material/Box';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import TreeView from '@mui/lab/TreeView';
import TreeItem from '@mui/lab/TreeItem';
import TextField from '@mui/material/TextField'
import { IconButton, Button } from '@mui/material';
import SyncAltIcon from '@mui/icons-material/SyncAlt';

// TODO: tmp using local datas
import _map_data from '../../../tmp/e2e4-map.json'
interface MappingObject {
    [key: string]: string;
}
const path_to_callId: MappingObject = _map_data;
const callId_to_path: MappingObject = Object.entries(path_to_callId).reduce((obj: MappingObject, [key, value]) => {
    obj[value] = key;
    return obj;
}, {});

declare global {
    var epg_highlight_nodes: string[];
}

globalThis.epg_highlight_nodes = ['0.30.8.23', '0.30.8.23.1', '0.30.8.23.1.1'];

type EPGInfoProps = {};

export const EPGInfo = () => {
    const [callId_value, set_callId_value] = React.useState('');
    const [path_value, set_path_value] = React.useState('');

    const handle_callId_input = (ev: React.KeyboardEvent) => {
        if (ev.key === 'Enter') {
            let val = '';
            if (callId_value !== '') {
                val = callId_to_path[callId_value] || 'wrong';
            }
            set_path_value(val);
        }
    };

    const handle_path_input = (ev: React.KeyboardEvent) => {
        if (ev.key === 'Enter') {
            let val = '';
            if (path_value !== '') {
                val = path_to_callId[path_value] || 'wrong';
            }
            set_callId_value(val);
        }
    };

    
    return (
        <Box
            component="form"
            sx={{ p: '10px 0px', display: 'flex', alignItems: 'center' }}
            noValidate
            autoComplete="off"
        >
            <TextField id='call-id-basic' label='callId' variant='outlined'
                value={callId_value}
                onChange={(ev) => {set_callId_value(ev.target.value);}}
                onKeyDown={handle_callId_input} />
            <SyncAltIcon />
            <TextField id='path-basic' label='path' variant='outlined'
                value={path_value}
                onChange={(ev) => {set_path_value(ev.target.value);}}
                onKeyDown={handle_path_input} />
        </Box>
    );
};