
import { createTheme } from '@mui/material/styles';
import type { } from '@mui/x-data-grid/themeAugmentation'; // Augment helper

const theme = createTheme({
    palette: {
        primary: {
            main: '#1a237e',
        },
        secondary: {
            main: '#c2185b',
        },
        background: {
            default: '#f4f6f8',
            paper: '#ffffff',
        },
    },
    typography: {
        fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
        h6: {
            fontWeight: 600,
        },
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    textTransform: 'none',
                },
            },
        },
        MuiDataGrid: {
            defaultProps: {
                density: 'compact',
                autoHeight: true,
            }
        }
    },
});

export default theme;
